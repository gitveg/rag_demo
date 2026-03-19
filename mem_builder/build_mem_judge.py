import os
import json
import time
from tqdm import tqdm
from openai import OpenAI
import dotenv

dotenv.load_dotenv()
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'

# ================= 配置 =================
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KB_DIR   = os.path.join(_BASE_DIR, "knowledge_base")

TEST_DIR             = os.path.join(_BASE_DIR, "tests", "synthetic_tests")
MEMORY_FILE          = os.path.join(_KB_DIR,   "genesis_error_memory.json")
EXECUTE_RESULTS_FILE = os.path.join(_KB_DIR,   "genesis_execute_results.json")
# 报错内容超过此长度不判官，避免消耗过多 token（如 GsTaichi 长 stack trace）
MAX_ERROR_LOG_CHARS = 8000

# 判官 LLM：OpenAI 兼容中转（如 ChatAnywhere），需环境变量 CHAT_API_KEY
judge_client = OpenAI(
    api_key=os.getenv("CHAT_API_KEY"),
    base_url="https://api.chatanywhere.tech/v1",
)
JUDGE_MODEL = "gemini-3-pro-preview"  # 可按中转站支持的模型修改，如 gpt-3.5-turbo

# 遇到 503 / 高负载时的重试
JUDGE_MAX_RETRIES = 4
JUDGE_RETRY_BASE_DELAY = 8.0

def _is_retryable_api_error(e):
    """是否为可重试的 API 错误（503、高负载等）"""
    msg = str(e).upper()
    return "503" in msg or "UNAVAILABLE" in msg or "HIGH DEMAND" in msg or "TRY AGAIN" in msg or "RATE" in msg

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            raw = f.read().strip()
            if not raw:
                return []
            return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []

def save_memory(data):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def analyze_error(code_path, error_log, file_id=None):
    """让 LLM 分析错误日志，提取规则。file_id 用作记忆 id，默认用文件名。"""
    if file_id is None:
        file_id = os.path.basename(code_path)
    with open(code_path, 'r', encoding='utf-8') as f:
        code_content = f.read()
    
    # 提取文件头部的 Query (我们在 gen 阶段写入的)
    query_line = code_content.split('\n')[1] if "User Query:" in code_content else "Unknown Context"
    
    print("   🕵️ Judge is analyzing the crash...")
    
    prompt = f"""
    Analyze the following Python Error in Genesis Physics Engine.
    
    Code Context:
    {code_content[:1000]}... (truncated)
    
    Error Log:
    {error_log}
    
    Task:
    1. Identify the 'Bad Pattern' (e.g., 'scene.add()', 'ViewerOptions(title=...)').
    2. Provide the 'Correction' (e.g., 'scene.add_entity()').
    3. Write a short 'Explanation' rule.
    4. If the error is trivial (syntax error, file not found), return NULL.
    
    Return JSON format:
    {{
        "bad_pattern": "scene.add(...)",
        "correction": "scene.add_entity(...)",
        "explanation": "Scene has no 'add' method. Use 'add_entity'.",
        "tags": ["api_mistake"]
    }}
    """
    
    last_error = None
    for attempt in range(JUDGE_MAX_RETRIES + 1):
        try:
            response = judge_client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            text = (response.choices[0].message.content or "").strip()
            if not text:
                return None

            clean_json = text.replace("```json", "").replace("```", "").strip()
            if "NULL" in clean_json or clean_json == "null":
                return None

            memory_item = json.loads(clean_json)

            # 添加元数据：id 用文件名，便于记忆去重
            memory_item["id"] = file_id
            memory_item["query_context"] = query_line

            return memory_item
        except Exception as e:
            last_error = e
            if attempt < JUDGE_MAX_RETRIES and _is_retryable_api_error(e):
                delay = JUDGE_RETRY_BASE_DELAY * (2 ** attempt)
                print(f"   ⏳ API busy (503/rate limit), retry in {delay:.0f}s ({attempt + 1}/{JUDGE_MAX_RETRIES})...")
                time.sleep(delay)
            else:
                break

    print(f"   ⚠️ Analysis failed: {last_error}")
    return None

def load_execute_results():
    """读取 build_mem_execute 生成的报错结果。"""
    if not os.path.exists(EXECUTE_RESULTS_FILE):
        return None
    with open(EXECUTE_RESULTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    if not os.path.exists(TEST_DIR):
        print(f"❌ No test directory: {TEST_DIR}. Run build_mem_gen.py first.")
        return

    data = load_execute_results()
    if not data or "results" not in data:
        print(f"❌ No execute results at {EXECUTE_RESULTS_FILE}. Run build_mem_execute.py first.")
        return

    results = data["results"]
    failures = [r for r in results if r.get("success") is False]
    if not failures:
        print("✅ No failures in execute results, nothing to judge.")
        return

    error_memory = load_memory()
    existing_ids = {item.get("id") for item in error_memory if item.get("id")}
    existing_patterns = {item.get("bad_pattern") for item in error_memory}
    new_count = 0

    print(f"🚀 Judging {len(failures)} failures from {EXECUTE_RESULTS_FILE}...")

    for rec in tqdm(failures, desc="Judging"):
        fname = rec.get("id")
        if not fname:
            continue
        path = os.path.join(TEST_DIR, fname)
        if not os.path.isfile(path):
            continue

        error_raw = rec.get("error_raw") or ""
        if "ModuleNotFoundError" in error_raw:
            continue

        if fname in existing_ids:
            continue

        error_log = (rec.get("error_extract") or rec.get("error_raw") or "").strip()
        if not error_log:
            continue
        if len(error_log) > MAX_ERROR_LOG_CHARS:
            print(f"\n⏭️ Skip judge: {fname} (error log too long: {len(error_log)} chars, max {MAX_ERROR_LOG_CHARS})")
            continue

        print(f"\n💥 Judge: {fname}")
        print("   --- Error excerpt ---")
        preview = error_log[:1500] + ("..." if len(error_log) > 1500 else "")
        print(preview)
        print("   --- end ---")

        analysis = analyze_error(path, error_log, file_id=fname)

        if analysis:
            if analysis.get("id") not in existing_ids and analysis.get("bad_pattern") not in existing_patterns:
                error_memory.append(analysis)
                existing_ids.add(analysis.get("id"))
                existing_patterns.add(analysis.get("bad_pattern"))
                new_count += 1
                print(f"   📝 Learned: {analysis['explanation']}")
            else:
                print("   (Skipping duplicate error pattern)")

    if new_count > 0:
        save_memory(error_memory)
        print(f"\n✅ Judge finished. Added {new_count} new error memories.")
    else:
        print("\n✅ Judge finished. No new errors to add.")

if __name__ == "__main__":
    main()
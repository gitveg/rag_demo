import json
import inspect
import genesis as gs
from llm_utils import LLMClient
from tqdm import tqdm

# ================= 配置 =================
INPUT_FILE = "genesis_knowledge_base_clean.json"
OUTPUT_FILE = "genesis_knowledge_base_final.json"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

# --- 核心修改：Prompt 聚焦于“填空” ---
SYSTEM_PROMPT = """
You are a Metadata Enrichment Agent for the Genesis Physics Engine API.
Your goal is to extract specific details from the raw docstring to fill in missing metadata.

Input: JSON object containing 'raw_docstring' and a 'tasks' object indicating what to generate.

Output: A JSON object with ONLY the requested fields:
1. "summary": (Generate ONLY if tasks.generate_summary is True) A concise 1-sentence summary.
2. "parameter_descs": A dictionary mapping "param_name" -> "description".
   - CRITICAL: Only provide descriptions for parameters that have specific UNITS (e.g., 'in meters'), CONSTRAINTS (e.g., 'must be > 0'), or AMBIGUITY.
   - CRITICAL: Leave the description EMPTY string "" if the parameter is self-explanatory (like 'color', 'pos', 'name').
   - Do NOT include type information in the description (we already have it).
3. "constraints": A list of strings extracting limitations/warnings (e.g., "Rigid does not support vis_mode").

Response Format: Pure JSON.
"""

def get_object_by_path(path):
    parts = path.split('.')
    current_obj = gs
    for part in parts[1:]:
        try:
            current_obj = getattr(current_obj, part)
        except AttributeError:
            return None
    return current_obj

def enrich_knowledge_base():
    llm = LLMClient(
        provider="openai", 
        api_key="sk-061e03c70f63402bb363bcd2960622d2",
        base_url="https://api.deepseek.com",
        model="deepseek-chat"
    )

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        kb_data = json.load(f)

    # 建议先跑前 5-10 个测试效果，正式跑时去掉切片
    # target_data = kb_data[:10]
    target_data = kb_data

    print(f"🚀 开始精准增强 {len(target_data)} 个 API...")
    print("   策略: 仅当 Summary 缺失时生成; 仅补充 Parameter Desc.")

    enriched_data = []
    
    for entry in tqdm(target_data, desc="Enriching", unit="api"):
        api_id = entry['api_id']
        current_summary = entry.get("summary", "No summary available.")
        
        # --- 1. 硬逻辑判断：是否需要生成 Summary ---
        needs_summary = (current_summary == "No summary available.")
        
        # --- 2. 回溯原始文档 ---
        obj = get_object_by_path(api_id)
        if obj is None:
            enriched_data.append(entry)
            continue
            
        raw_doc = inspect.getdoc(obj)
        if not raw_doc:
            enriched_data.append(entry)
            continue

        # --- 3. 构建精简 User Content ---
        user_content = json.dumps({
            "api_name": api_id,
            "signature": entry['signature'],
            "raw_docstring": raw_doc,
            "parameter_list": [p['name'] for p in entry['parameters']], # 只给名字，不给type，防止LLM干扰
            "tasks": {
                "generate_summary": needs_summary, # 明确告诉 LLM 任务开关
                "extract_parameter_descs": True,
                "extract_constraints": True
            }
        }, indent=2)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        try:
            response = llm.chat(messages, temperature=0.1)
            response = response.replace("```json", "").replace("```", "").strip()
            ai_result = json.loads(response)
            
            log_msg = [f"\n{Colors.HEADER}--- API: {api_id} ---{Colors.ENDC}"]

            # --- 4. 回填逻辑 (只填空，不覆盖) ---

            # A. 处理 Summary
            if needs_summary:
                new_sum = ai_result.get("summary")
                if new_sum:
                    entry["summary"] = new_sum
                    log_msg.append(f"{Colors.GREEN}[Summary Generated]: {new_sum}{Colors.ENDC}")
            else:
                # 原有的很好，保持不变 (不做任何操作)
                # log_msg.append(f"{Colors.BLUE}[Summary Kept]{Colors.ENDC}") 
                pass

            # B. 处理 Parameters (只更新 desc)
            # LLM 返回的是 {"material": "Must be Rigid", "max_particles": ""}
            ai_param_descs = ai_result.get("parameter_descs", {})
            updated_params = []
            
            for param in entry["parameters"]:
                p_name = param["name"]
                # 只有当 LLM 提供了该参数的描述，且描述不为空时，才更新 desc
                if p_name in ai_param_descs and ai_param_descs[p_name]:
                    param["desc"] = ai_param_descs[p_name]
                    updated_params.append(p_name)
            
            if updated_params:
                log_msg.append(f"{Colors.CYAN}[Desc Filled]: {', '.join(updated_params)}{Colors.ENDC}")

            # C. 处理 Constraints
            new_constraints = ai_result.get("constraints", [])
            if new_constraints:
                entry["constraints"] = new_constraints
                log_msg.append(f"{Colors.RED}[Constraints]: {new_constraints}{Colors.ENDC}")

            # 仅当有实质性更新时才打印，保持控制台清爽
            if needs_summary or updated_params or new_constraints:
                tqdm.write("\n".join(log_msg))

        except Exception as e:
            tqdm.write(f"{Colors.RED}[Error] {api_id}: {e}{Colors.ENDC}")
        
        enriched_data.append(entry)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(enriched_data, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ 增强完成！结果已保存至: {OUTPUT_FILE}")

if __name__ == "__main__":
    enrich_knowledge_base()
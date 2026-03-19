"""
执行 synthetic_tests/ 下所有用例，将运行失败的文件及完整报错信息格式化存储，
供 build_mem_judge 直接读取分析，避免判官阶段重复执行。
"""
import os
import json
import subprocess
import sys
from datetime import datetime
from tqdm import tqdm

# ================= 配置 =================
_BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KB_DIR     = os.path.join(_BASE_DIR, "knowledge_base")

TEST_DIR    = os.path.join(_BASE_DIR, "tests", "synthetic_tests")
OUTPUT_FILE = os.path.join(_KB_DIR,   "genesis_execute_results.json")
# 成功用例可能含编译/运行，约 2 分钟，设大一些
RUN_TIMEOUT = 150  # 秒

TRACEBACK_START = "Traceback (most recent call last):"
GENESIS_ERROR_MARKER = "[Genesis]"
ERROR_MARKER = "[ERROR]"


def extract_error_segment(raw_output: str) -> str:
    """
    从完整输出中截取「完整报错信息」：
    从 "Traceback (most recent call last):" 开头，
    到包含 "[Genesis] ... [ERROR] ..." 的那一行结尾。
    若找不到开头则返回整段输出。
    """
    if not raw_output or not raw_output.strip():
        return raw_output
    start = raw_output.find(TRACEBACK_START)
    if start == -1:
        return raw_output.strip()

    # 从 Traceback 往后找第一行同时包含 [Genesis] 和 [ERROR] 的作为结尾
    rest = raw_output[start:]
    lines = rest.split("\n")
    end_line_idx = -1
    for i, line in enumerate(lines):
        if GENESIS_ERROR_MARKER in line and ERROR_MARKER in line:
            end_line_idx = i
            break
    if end_line_idx >= 0:
        segment = "\n".join(lines[: end_line_idx + 1])
    else:
        segment = rest
    return segment.strip()


def run_one(path: str, fname: str, env: dict) -> dict:
    """执行单个文件，返回 { id, success, error_raw?, error_extract? }"""
    try:
        result = subprocess.run(
            [sys.executable, "-u", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=RUN_TIMEOUT,
        )
        raw = (result.stdout or "").strip()
        if result.returncode == 0:
            return {"id": fname, "success": True}
        return {
            "id": fname,
            "success": False,
            "error_raw": raw,
            "error_extract": extract_error_segment(raw),
        }
    except subprocess.TimeoutExpired:
        return {
            "id": fname,
            "success": False,
            "error_raw": f"(Timeout after {RUN_TIMEOUT}s)",
            "error_extract": f"(Timeout after {RUN_TIMEOUT}s)",
        }
    except Exception as e:
        return {
            "id": fname,
            "success": False,
            "error_raw": str(e),
            "error_extract": str(e),
        }


def main():
    if not os.path.exists(TEST_DIR):
        print(f"❌ No test directory: {TEST_DIR}. Run build_mem_gen.py first.")
        return

    files = sorted(f for f in os.listdir(TEST_DIR) if f.endswith(".py"))
    if not files:
        print("❌ No .py files in synthetic_tests.")
        return

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"

    print(f"🚀 Executing {len(files)} tests (timeout={RUN_TIMEOUT}s each)...")
    results = []
    for fname in tqdm(files, desc="Execute"):
        path = os.path.join(TEST_DIR, fname)
        results.append(run_one(path, fname, env))

    out = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "timeout_seconds": RUN_TIMEOUT,
        "results": results,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    n_fail = sum(1 for r in results if not r.get("success"))
    print(f"\n✅ Done. Failures: {n_fail}/{len(results)} → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

"""
run_and_collect.py — 执行闭环的"生成→执行→收集"一体化脚本。

在 rag_demo 内完成：读取 prompts → agent.solve() → 执行代码 → 收集结果到 execution_log.jsonl。

这是执行闭环的 Runtime 层，与 processor.py（离线处理层）配合使用。

用法：
    # 用 benchmark query.json 的 prompts 运行并收集
    python run_and_collect.py --prompts benchmark/query.json

    # 指定输出日志路径
    python run_and_collect.py --prompts benchmark/query.json --log workspace/logs/exec_log.jsonl

    # 只跑前 5 个（测试）
    python run_and_collect.py --prompts benchmark/query.json --max-prompts 5

    # 跑完后自动执行反馈处理器
    python run_and_collect.py --prompts benchmark/query.json --auto-process

完整闭环：
    1. run_and_collect.py  → 生成 execution_log.jsonl
    2. processor.py --log execution_log.jsonl  → 回写知识库
    3. python rag_engine.py  → 重新灌库
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time

# Windows GBK 兼容：强制 stdout/stderr 使用 UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAG_DEMO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, RAG_DEMO_ROOT)
sys.path.insert(0, SCRIPT_DIR)

from event_schema import (
    SCHEMA_VERSION,
    environment_fingerprint,
    make_event_id,
    make_run_id,
    sanitize_task_id,
    sha256_text,
)
from failure_classifier import classify_execution_result


# ==================== 配置 ====================

DEFAULT_PROMPTS = os.path.join(RAG_DEMO_ROOT, "benchmark", "query.json")
DEFAULT_LOG_DIR = os.path.join(RAG_DEMO_ROOT, "workspace", "logs")
DEFAULT_TIMEOUT = 150  # 秒
GENESIS_ENV_FLAG = "GENESIS_OFFSCREEN"

# ==================== 执行结果分析 ====================

def analyze_execution(stdout: str, stderr: str, returncode: int) -> dict:
    """分析执行结果，返回结构化信号（与 phys_agent/utils/runner.py 对齐）。"""
    combined = f"{stdout}\n{stderr}".strip()

    signals = {
        "returncode": returncode,
        "scene_created": "[Genesis]" in combined and "Scene <" in combined and "created." in combined,
        "scene_build_started": "Building scene" in combined,
        "kernels_compiled": "Compiling simulation kernels" in combined,
        "viewer_created": "Viewer created." in combined,
        "fps_reported": "Running at " in combined,
        "video_saved": "Video saved." in combined,
        "traceback_detected": "Traceback (most recent call last):" in combined,
        "genesis_error_detected": "[Genesis]" in combined and "[ERROR]" in combined,
        "genesis_exception_detected": "GenesisException" in combined,
    }

    signals["appears_successful_run"] = (
        returncode == 0
        and not signals["traceback_detected"]
        and not signals["genesis_error_detected"]
        and not signals["genesis_exception_detected"]
        and signals["scene_build_started"]
    )

    # Backend-agnostic process signal. This is not a physics verification signal.
    best_effort_success = (
        returncode == 0
        and not signals["traceback_detected"]
        and not signals["genesis_error_detected"]
        and not signals["genesis_exception_detected"]
    )

    phase_summary = []
    for key in ["scene_created", "scene_build_started", "kernels_compiled",
                 "viewer_created", "fps_reported", "video_saved"]:
        if signals.get(key):
            phase_summary.append(key)
    signals["phase_summary"] = phase_summary

    # 提取简洁错误
    error_match = re.search(r"Traceback \(most recent call last\):(.*)", combined, re.DOTALL)
    concise_error = error_match.group(0).strip() if error_match else stderr.strip()

    error_type = None
    if not (signals["appears_successful_run"] or best_effort_success):
        matches = re.findall(r"\b([A-Za-z_]\w*(?:Error|Exception)):\s*[^\n]+", concise_error)
        error_type = matches[-1] if matches else ("RuntimeError" if returncode != 0 else "ExecutionError")

    result = {
        "success": signals["appears_successful_run"] or best_effort_success,
        "verified_success": False,
        "best_effort_success": best_effort_success,
        "string_based_success": signals["appears_successful_run"],
        "error_type": error_type,
        "execution_analysis": signals,
        "concise_error": concise_error,
        "stdout": stdout,
        "stderr": stderr,
    }
    outcome, category = classify_execution_result(result)
    result["outcome"] = outcome
    result["failure_category"] = category
    return result


# ==================== 代码执行 ====================

def execute_code(code_path: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """执行代码文件并返回结构化结果。"""
    env = os.environ.copy()
    env.setdefault(GENESIS_ENV_FLAG, "1")
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    try:
        proc = subprocess.run(
            [sys.executable, code_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        result = analyze_execution(proc.stdout or "", proc.stderr or "", proc.returncode)
        return result
    except subprocess.TimeoutExpired as exc:
        stdout = _coerce_output(exc.stdout)
        stderr = _coerce_output(exc.stderr)
        timeout_message = f"TimeoutExpired after {timeout}s"
        concise = "\n".join(x for x in (stdout, stderr, timeout_message) if x).strip()
        result = {
            "success": False,
            "verified_success": False,
            "error_type": "TimeoutError",
            "execution_analysis": {"appears_successful_run": False, "phase_summary": [], "returncode": None},
            "concise_error": concise,
            "stdout": stdout,
            "stderr": stderr or timeout_message,
        }
        result["outcome"], result["failure_category"] = classify_execution_result(result)
        return result
    except Exception as e:
        result = {
            "success": False,
            "verified_success": False,
            "error_type": type(e).__name__,
            "execution_analysis": {"appears_successful_run": False, "phase_summary": [], "returncode": None},
            "concise_error": str(e),
            "stdout": "",
            "stderr": str(e),
        }
        result["outcome"], result["failure_category"] = classify_execution_result(result)
        return result


def _coerce_output(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _write_artifact(path: str, content: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content or "")
    return path


# ==================== 日志收集 ====================

def write_execution_log(log_path: str, record: dict):
    """追加一条记录到 JSONL 日志。"""
    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ==================== 主流程 ====================

def run(prompts_file: str, log_path: str, max_prompts: int = 0,
        start_index: int = 0,
        rewrite_mode: str = "hyde", timeout: int = DEFAULT_TIMEOUT,
        auto_process: bool = False, run_id: str = ""):
    """执行完整的 生成→执行→收集 循环。"""

    # 加载 prompts
    with open(prompts_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_prompts = data if isinstance(data, list) else data.get("prompts", [])
    start_index = max(0, start_index)
    indexed_prompts = list(enumerate(all_prompts))[start_index:]
    if max_prompts > 0:
        indexed_prompts = indexed_prompts[:max_prompts]
    run_id = sanitize_task_id(run_id, fallback=make_run_id()) if run_id else make_run_id()
    environment = environment_fingerprint()

    print(f"\n{'=' * 70}")
    print(f"执行闭环 — 生成→执行→收集")
    print(f"{'=' * 70}")
    print(f"Prompts: {len(indexed_prompts)} 条（来源: {prompts_file}）")
    print(f"Start index: {start_index}")
    print(f"Run ID: {run_id}")
    print(f"日志输出: {log_path}")
    print(f"Rewrite 模式: {rewrite_mode}")
    print(f"超时: {timeout}s")
    print()

    # 初始化 Agent
    from agent import GenesisAgent
    agent = None
    agent_init_error = ""
    try:
        agent = GenesisAgent(rewrite_mode=rewrite_mode)
    except Exception as exc:
        agent_init_error = f"{type(exc).__name__}: {exc}"
        print(f"[FAIL] Agent 初始化失败，所有选中 prompt 将记录 generation_failed: {agent_init_error}")

    # 统计
    total = len(indexed_prompts)
    success_count = 0
    fail_count = 0
    error_count = 0
    start_time = time.time()

    for i, (prompt_index, item) in enumerate(indexed_prompts, 1):
        raw_task_id = item.get("task_id", f"task_{prompt_index:03d}")
        task_id = sanitize_task_id(raw_task_id, fallback=f"task_{prompt_index:03d}")
        query = item.get("query", "")
        if not query:
            query = ""

        short_q = re.sub(r"\s+", " ", query).strip()[:80]
        print(f"\n{'─' * 60}")
        print(f"[{i}/{total}] {task_id}: {short_q}{'...' if len(query) > 80 else ''}")
        print(f"{'─' * 60}")

        # Step 1: Agent 生成代码
        t0 = time.time()
        generation_error = ""
        try:
            if not query:
                raise ValueError("Empty query")
            if agent is None:
                raise RuntimeError(f"Agent initialization failed: {agent_init_error}")
            result = agent.solve(query, save_code=False)
            code = result.get("code", "")
        except Exception as e:
            print(f"  [FAIL] Agent 生成失败: {e}")
            code = ""
            result = {}
            generation_error = f"{type(e).__name__}: {e}"

        gen_elapsed = time.time() - t0
        print(f"  生成耗时: {gen_elapsed:.1f}s | 代码长度: {len(code)} chars")

        if not code or code.startswith("# Error:"):
            print(f"  [SKIP]️ 跳过执行（生成失败）")
            fail_count += 1
            error_count += 1
            artifact_task_id = f"{prompt_index:03d}_{task_id}"
            artifact_dir = os.path.join(
                RAG_DEMO_ROOT, "workspace", "runs", run_id, artifact_task_id, "attempt_1"
            )
            error_text = generation_error or code or "Empty code generated"
            error_path = _write_artifact(os.path.join(artifact_dir, "generation_error.txt"), error_text)
            outcome, category = classify_execution_result(
                {"success": False, "error_type": "GenerationError", "concise_error": error_text},
                generation_failed=True,
            )
            record = {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "task_id": task_id,
                "source_task_id": raw_task_id,
                "prompt_index": prompt_index,
                "prompt_hash": sha256_text(query),
                "environment": environment,
                "attempt": 1,
                "stage": "generation",
                "success": False,
                "verified_success": False,
                "outcome": outcome,
                "failure_category": category,
                "error_type": "GenerationError",
                "concise_error": error_text,
                "stderr": error_text[:8000],
                "stdout": "",
                "query": query,
                "code_path": "",
                "code_sha256": "",
                "artifacts": {"generation_error": error_path},
                "execution_analysis": {},
                "gen_elapsed_sec": round(gen_elapsed, 1),
                "exec_elapsed_sec": 0.0,
                "key_apis": result.get("key_apis", []),
                "knowledge_ids": result.get("knowledge_ids", []),
                "retrieval_trace": [
                    {"knowledge_id": kid, "rank": rank}
                    for rank, kid in enumerate(result.get("knowledge_ids", []), 1)
                ],
                "rewrite_mode": rewrite_mode,
                "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            }
            record["event_id"] = make_event_id(
                run_id, task_id, prompt_index, 1, "generation", ""
            )
            write_execution_log(log_path, record)
            continue

        # Step 2: 保存不可变代码产物
        artifact_task_id = f"{prompt_index:03d}_{task_id}"
        artifact_dir = os.path.join(
            RAG_DEMO_ROOT, "workspace", "runs", run_id, artifact_task_id, "attempt_1"
        )
        code_path = _write_artifact(os.path.join(artifact_dir, "code.py"), code)
        code_sha256 = sha256_text(code)

        # Step 3: 执行代码
        print(f"  [EXEC] 执行中...")
        t1 = time.time()
        exec_result = execute_code(code_path, timeout=timeout)
        exec_elapsed = time.time() - t1
        stdout_path = _write_artifact(os.path.join(artifact_dir, "stdout.txt"), exec_result.get("stdout", ""))
        stderr_path = _write_artifact(os.path.join(artifact_dir, "stderr.txt"), exec_result.get("stderr", ""))
        traceback_path = _write_artifact(
            os.path.join(artifact_dir, "traceback.txt"), exec_result.get("concise_error", "")
        )

        is_success = exec_result["success"]
        if is_success:
            success_count += 1
            print(f"  [OK] 执行成功 ({exec_elapsed:.1f}s)")
        else:
            fail_count += 1
            error_type = exec_result.get("error_type", "unknown")
            print(f"  [FAIL] 执行失败: {error_type} ({exec_elapsed:.1f}s)")

        # Step 4: 收集到日志
        record = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "task_id": task_id,
            "source_task_id": raw_task_id,
            "prompt_index": prompt_index,
            "prompt_hash": sha256_text(query),
            "environment": environment,
            "query": query,
            "code_path": code_path,
            "code_sha256": code_sha256,
            "attempt": 1,
            "stage": "execution",
            "success": is_success,
            "verified_success": exec_result.get("verified_success", False),
            "outcome": exec_result.get("outcome", "runtime_failed"),
            "failure_category": exec_result.get("failure_category", "runtime"),
            "error_type": exec_result.get("error_type", ""),
            "concise_error": exec_result.get("concise_error", "")[:8000],
            "stderr": exec_result.get("stderr", "")[:8000],
            "stdout": exec_result.get("stdout", "")[:2000],
            "artifacts": {
                "code": code_path,
                "stdout": stdout_path,
                "stderr": stderr_path,
                "traceback": traceback_path,
            },
            "execution_analysis": exec_result.get("execution_analysis", {}),
            "gen_elapsed_sec": round(gen_elapsed, 1),
            "exec_elapsed_sec": round(exec_elapsed, 1),
            "key_apis": result.get("key_apis", []),
            "knowledge_ids": result.get("knowledge_ids", []),
            "retrieval_trace": [
                {"knowledge_id": kid, "rank": rank}
                for rank, kid in enumerate(result.get("knowledge_ids", []), 1)
            ],
            "rewrite_mode": rewrite_mode,
        }
        record["event_id"] = make_event_id(
            run_id, task_id, prompt_index, 1, "execution", code_sha256
        )
        write_execution_log(log_path, record)

    total_elapsed = time.time() - start_time

    # 汇总
    print(f"\n{'=' * 70}")
    print(f"运行完成")
    print(f"{'=' * 70}")
    print(f"  总计: {total} | [OK] 成功: {success_count} | [FAIL] 失败: {fail_count} | [WARN]️ 错误: {error_count}")
    print(f"  总耗时: {total_elapsed:.0f}s ({total_elapsed / 60:.1f}min)")
    print(f"  日志: {log_path}")

    # 自动执行反馈处理器
    if auto_process and (success_count + fail_count) > 0:
        print(f"\n{'=' * 70}")
        print(f"自动执行反馈处理器...")
        print(f"{'=' * 70}")
        processor_path = os.path.join(SCRIPT_DIR, "processor.py")
        if os.path.exists(processor_path):
            proc = subprocess.run(
                [sys.executable, processor_path, "--log", log_path, "--loops", "bc"],
                cwd=SCRIPT_DIR,
            )
            if proc.returncode == 0:
                print("  [OK] 反馈处理完成")
            else:
                print(f"  [WARN]️ 反馈处理失败 (exit={proc.returncode})")
        else:
            print(f"  [WARN]️ 找不到处理器: {processor_path}")


def main():
    parser = argparse.ArgumentParser(description="执行闭环 — 生成→执行→收集")
    parser.add_argument("--prompts", default=DEFAULT_PROMPTS, help="Prompts JSON 文件路径")
    parser.add_argument("--log", default="", help="输出日志路径（默认自动生成）")
    parser.add_argument("--max-prompts", type=int, default=0, help="最多跑几个 prompt（0=全部）")
    parser.add_argument("--start-index", type=int, default=0, help="从第几个 prompt 开始跑（0-based）")
    parser.add_argument("--rewrite-mode", choices=["none", "translate", "hyde"], default="hyde")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="代码执行超时（秒）")
    parser.add_argument("--auto-process", action="store_true", help="跑完后自动执行反馈处理器")
    parser.add_argument("--run-id", default="", help="可选运行 ID；默认自动生成")

    args = parser.parse_args()

    # 自动生成日志路径
    log_path = args.log
    if not log_path:
        os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(DEFAULT_LOG_DIR, f"execution_log_{stamp}.jsonl")

    run(
        prompts_file=args.prompts,
        log_path=log_path,
        max_prompts=args.max_prompts,
        start_index=args.start_index,
        rewrite_mode=args.rewrite_mode,
        timeout=args.timeout,
        auto_process=args.auto_process,
        run_id=args.run_id,
    )


if __name__ == "__main__":
    main()

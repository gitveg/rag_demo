#!/usr/bin/env python3
"""
RAG vs No-RAG 对比实验
=====================
对 10 个任务分别运行：
  A) No RAG  — 直接让 LLM 生成代码，不提供任何检索上下文
  B) Best RAG — hyde + unit + rerank(top_n=10) + SymbolMatcher + 满配检索数量

对比 Pass@1 / Pass@3 代码执行成功率。

用法：
  cd rag_demo/
  python benchmark/scripts/run_rag_vs_no_rag.py
"""

import json, os, sys, time, subprocess, shutil
from datetime import datetime
from typing import List, Tuple

# ── path setup ──────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
_BENCH_DIR = os.path.join(_ROOT, "benchmark")

from benchmark.metrics import compute_pass_at_k, get_success_attempt


# ── constants ───────────────────────────────────────────────────
# 默认代表性子集（10 个：4 simple + 3 medium + 3 hard）；--all 跑全部 100 个
DEFAULT_TASK_IDS = [
    "eval_001", "eval_002", "eval_003", "eval_004",
    "eval_006", "eval_007", "eval_008",
    "eval_016", "eval_017", "eval_018",
]

MAX_RETRIES = 3        # Pass@3（可用 --max-retries 覆盖）
EXEC_TIMEOUT = 600     # 秒

BEST_RAG_PARAMS = {
    "rewrite_mode":     "hyde",
    "hyde_route":       "unit",
    "n_api":            10,
    "n_code":           3,
    "n_snippet":        5,
    "n_error":          0,
    "n_units":          10,
    "tag_filter":       None,
    "include_core_api": True,
    "core_api_limit":   40,
    "rerank":           True,
    "rerank_top_n":     10,
    "rerank_oversample": 2.0,
    "use_hybrid":       True,   # SymbolMatcher
}


# ── helpers ─────────────────────────────────────────────────────

# Taichi/GSTaichi kernel 编译缓存锁。超时/崩溃的子进程会留下 0 字节僵尸锁，
# 后续需要编译新 kernel 的任务会因抢不到锁而失败（ ticache.lock failed）。
# 每次执行前删掉它，确保干净的锁状态。
_TI_CACHE_DIR = os.path.join(os.environ.get("GSTAICHI_CACHE", "C:/gstaichi_cache"),
                             "ticache", "kernel_compilation_manager")
_TI_LOCK_FILE = os.path.join(_TI_CACHE_DIR, "ticache.lock")


def _clean_ti_lock():
    """删除 GSTaichi kernel 编译缓存的僵尸锁文件（若存在）。"""
    try:
        if os.path.isfile(_TI_LOCK_FILE):
            os.remove(_TI_LOCK_FILE)
    except Exception:
        pass


def _execute_code(code: str, task_id: str, label: str) -> Tuple[bool, str]:
    """Write code to temp file, run it, return (success, output)."""
    _clean_ti_lock()  # 防止上一轮残留的僵尸锁搞死本次执行
    tmp_dir = os.path.join(_BENCH_DIR, "results", "tests")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"cmp_{label}_{task_id}.py")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(code)
    env = os.environ.copy()
    env["GENESIS_OFFSCREEN"] = "1"
    env["PYTEST_VERSION"] = "1"
    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True,
            timeout=EXEC_TIMEOUT, env=env, cwd=tmp_dir,
        )
        success = proc.returncode == 0
        output = (proc.stdout + proc.stderr)[-500:]
        return success, output
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {EXEC_TIMEOUT}s"
    except Exception as e:
        return False, str(e)


def _run_attempts(agent, query: str, task_id: str, label: str,
                  knowledge_list=None, rag_params: dict = None,
                  max_retries: int = MAX_RETRIES) -> dict:
    """Run up to max_retries attempts, return execution result dict."""
    attempts = []
    for attempt in range(1, max_retries + 1):
        try:
            if rag_params is not None:
                # Best RAG: 每次重新检索（query 相同但可能有不同结果）
                from rag_engine import GenesisRAG
                rag = GenesisRAG(reset_db=False)
                ctx = rag.search(query, **rag_params)
                solve_result = agent.solve(query, knowledge_list=ctx, save_code=False)
            elif knowledge_list is not None:
                # No RAG: 空列表
                solve_result = agent.solve(query, knowledge_list=knowledge_list, save_code=False)
            else:
                solve_result = agent.solve(query, save_code=False)
            code = solve_result.get("code", "")
        except Exception as e:
            print(f"      [Attempt {attempt}] Generation error: {e}")
            attempts.append({"attempt": attempt, "success": False, "error": str(e)})
            continue

        if not code or code.startswith("# Error"):
            print(f"      [Attempt {attempt}] Empty/error code")
            attempts.append({"attempt": attempt, "success": False, "error": "empty code"})
            continue

        success, output = _execute_code(code, task_id, label)
        tag = "OK" if success else "FAIL"
        print(f"      [Attempt {attempt}] {tag}")
        attempts.append({
            "attempt": attempt,
            "success": success,
            "code": code,
            "error": output if not success else None,
        })
        if success:
            break

    return {
        "pass_at_1": compute_pass_at_k(attempts, 1),
        "pass_at_3": compute_pass_at_k(attempts, 3),
        "success_attempt": get_success_attempt(attempts),
        "total_attempts": len(attempts),
        "attempts": attempts,
    }


# ── CLI ─────────────────────────────────────────────────────────

def _parse_args():
    import argparse
    p = argparse.ArgumentParser(
        description="RAG vs No-RAG 对比实验（带执行）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 默认 10 个代表性任务
  python benchmark/scripts/run_rag_vs_no_rag.py

  # 全量 100 个任务
  python benchmark/scripts/run_rag_vs_no_rag.py --all

  # 指定任务子集
  python benchmark/scripts/run_rag_vs_no_rag.py --tasks eval_001,eval_002

  # 自定义输出目录（默认 comparisons/rag_vs_no_rag[_full]）
  python benchmark/scripts/run_rag_vs_no_rag.py --all --output-dir benchmark/results/comparisons/my_run

断点续跑：默认会读取 --output-dir 下的 result.json，跳过已完成的 task_id。
        加 --no-resume 可强制从头重跑（会覆盖）。
""",
    )
    p.add_argument("--all", action="store_true", help="跑 query.json 全部任务（100 条）")
    p.add_argument("--tasks", type=str, default=None, metavar="ID1,ID2,...",
                   help="指定 task_id（逗号分隔）")
    p.add_argument("--output-dir", type=str, default=None, help="结果输出目录")
    p.add_argument("--max-retries", type=int, default=MAX_RETRIES, metavar="K",
                   help=f"每个任务最大尝试次数（默认 {MAX_RETRIES}，对应 Pass@K）")
    p.add_argument("--no-resume", action="store_true",
                   help="不读取已有 result.json，从头重跑")
    return p.parse_args()


# ── main ────────────────────────────────────────────────────────

def main():
    args = _parse_args()

    # ── 解析任务集 ──────────────────────────────────
    qpath = os.path.join(_BENCH_DIR, "query.json")
    all_tasks = json.load(open(qpath, "r", encoding="utf-8"))
    task_map = {t["task_id"]: t for t in all_tasks}

    if args.all:
        tasks = all_tasks
        run_kind = "full"
    elif args.tasks:
        ids = [s.strip() for s in args.tasks.split(",") if s.strip()]
        tasks = [task_map[i] for i in ids if i in task_map]
        run_kind = "subset"
    else:
        tasks = [task_map[i] for i in DEFAULT_TASK_IDS if i in task_map]
        run_kind = "default"

    # ── 输出目录 ────────────────────────────────────
    if args.output_dir:
        out_dir = args.output_dir
    elif run_kind == "full":
        out_dir = os.path.join(_BENCH_DIR, "results", "comparisons", "rag_vs_no_rag_full")
    else:
        out_dir = os.path.join(_BENCH_DIR, "results", "comparisons", "rag_vs_no_rag")
    os.makedirs(out_dir, exist_ok=True)
    result_path = os.path.join(out_dir, "result.json")

    max_retries = args.max_retries
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

    print("=" * 64)
    print("  RAG vs No-RAG Comparison Benchmark")
    print(f"  Tasks: {len(tasks)} ({run_kind})  |  Max retries: {max_retries}")
    print(f"  Model: {model}")
    print(f"  Output: {out_dir}")
    print(f"  Best RAG params: hyde+unit+rerank(10)+SymbolMatcher")
    print("=" * 64)

    # ── 断点续跑：读取已有结果 ──────────────────────
    results_no_rag: List[dict] = []
    results_best_rag: List[dict] = []
    if not args.no_resume and os.path.isfile(result_path):
        try:
            prev = json.load(open(result_path, encoding="utf-8"))
            results_no_rag = prev.get("tasks", {}).get("no_rag", []) or []
            results_best_rag = prev.get("tasks", {}).get("best_rag", []) or []
            done_ids = {t["task_id"] for t in results_no_rag}
            print(f"  [Resume] 已有 {len(done_ids)} 个任务结果，将跳过：{sorted(done_ids)}\n")
        except Exception as e:
            print(f"  [Resume] 读取旧结果失败({e})，从头开始\n")
            results_no_rag, results_best_rag = [], []
    else:
        print()

    # lazy imports（放在断点逻辑之后，避免 --no-resume 时也加载重模块）
    from agent import GenesisAgent

    done_ids = {t["task_id"] for t in results_no_rag}
    pending = [(i, t) for i, t in enumerate(tasks) if t["task_id"] not in done_ids]

    def _save_incremental():
        """把当前结果写到 result.json（每个任务跑完后调用，防中断丢失）。"""
        n = len(tasks)
        p1a = sum(1 for r in results_no_rag if r.get("pass_at_1"))
        p3a = sum(1 for r in results_no_rag if r.get("pass_at_3"))
        p1b = sum(1 for r in results_best_rag if r.get("pass_at_1"))
        p3b = sum(1 for r in results_best_rag if r.get("pass_at_3"))
        payload = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "max_retries": max_retries,
            "best_rag_params": BEST_RAG_PARAMS,
            "task_ids": [t["task_id"] for t in tasks],
            "task_count_total": n,
            "task_count_done": len(results_no_rag),
            "summary": {
                "no_rag":   {"pass_at_1": p1a, "pass_at_3": p3a, "n": len(results_no_rag)},
                "best_rag": {"pass_at_1": p1b, "pass_at_3": p3b, "n": len(results_best_rag)},
            },
            "tasks": {
                "no_rag":   results_no_rag,
                "best_rag": results_best_rag,
            },
        }
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    # ── 主循环 ──────────────────────────────────────
    for idx, (i, task) in enumerate(pending):
        tid = task["task_id"]
        query = task["query"]
        print(f"\n{'─'*60}")
        print(f"[{i+1:02d}/{len(tasks)}] {tid} ({task['complexity']})  "
              f"(pending {idx+1}/{len(pending)})")
        print(f"  Query: {query[:80]}")

        # A) No RAG
        print(f"  ── A) No RAG ──")
        agent_a = GenesisAgent(rewrite_mode="none", hyde_route="unit")
        t0 = time.time()
        res_a = _run_attempts(agent_a, query, tid, "no_rag", knowledge_list=[],
                              max_retries=max_retries)
        res_a["duration"] = round(time.time() - t0, 1)
        res_a["task_id"] = tid
        res_a["complexity"] = task["complexity"]
        results_no_rag.append(res_a)
        print(f"    → P@1={'OK' if res_a['pass_at_1'] else 'FAIL'}  "
              f"P@3={'OK' if res_a['pass_at_3'] else 'FAIL'}  "
              f"({res_a['duration']}s)")

        # B) Best RAG
        print(f"  ── B) Best RAG (hyde+unit+rerank+SymbolMatcher) ──")
        agent_b = GenesisAgent(rewrite_mode="hyde", hyde_route="unit")
        t0 = time.time()
        res_b = _run_attempts(agent_b, query, tid, "best_rag", rag_params=BEST_RAG_PARAMS,
                              max_retries=max_retries)
        res_b["duration"] = round(time.time() - t0, 1)
        res_b["task_id"] = tid
        res_b["complexity"] = task["complexity"]
        results_best_rag.append(res_b)
        print(f"    → P@1={'OK' if res_b['pass_at_1'] else 'FAIL'}  "
              f"P@3={'OK' if res_b['pass_at_3'] else 'FAIL'}  "
              f"({res_b['duration']}s)")

        # 每个任务跑完立即落盘
        _save_incremental()

    # ── Summary ────────────────────────────────────
    n = len(results_no_rag)
    print(f"\n\n{'='*64}")
    print("  RESULTS SUMMARY")
    print(f"{'='*64}\n")

    hdr = f"  {'task_id':<24} {'cx':<8} │ {'No RAG':^16} │ {'Best RAG':^16} │"
    sep = f"  {'─'*24} {'─'*8} ┼ {'─'*16} ┼ {'─'*16} ┤"
    print(hdr)
    print(sep)

    p1_a_total = p3_a_total = p1_b_total = p3_b_total = 0
    by_id_a = {t["task_id"]: t for t in results_no_rag}
    by_id_b = {t["task_id"]: t for t in results_best_rag}
    for task in tasks:
        tid = task["task_id"]
        ra, rb = by_id_a.get(tid), by_id_b.get(tid)
        if not ra or not rb:
            continue
        cx = ra["complexity"]
        p1a = "OK" if ra["pass_at_1"] else "FAIL"
        p3a = "OK" if ra["pass_at_3"] else "FAIL"
        p1b = "OK" if rb["pass_at_1"] else "FAIL"
        p3b = "OK" if rb["pass_at_3"] else "FAIL"
        p1_a_total += int(ra["pass_at_1"])
        p3_a_total += int(ra["pass_at_3"])
        p1_b_total += int(rb["pass_at_1"])
        p3_b_total += int(rb["pass_at_3"])
        print(f"  {tid:<24} {cx:<8} │ {p1a:^6} {p3a:^6} │ {p1b:^6} {p3b:^6} │")

    print(sep)
    print(f"  {'TOTAL':<24} {'':8} │ "
          f"{p1_a_total:>3}/{n} {p3_a_total:>4}/{n} │ "
          f"{p1_b_total:>3}/{n} {p3_b_total:>4}/{n} │")
    if n:
        print(f"  {'RATE':<24} {'':8} │ "
              f"  {p1_a_total/n*100:>3.0f}%   {p3_a_total/n*100:>3.0f}%  │ "
              f"  {p1_b_total/n*100:>3.0f}%   {p3_b_total/n*100:>3.0f}%  │")
        print(f"\n  No RAG  → Pass@1: {p1_a_total}/{n} ({p1_a_total/n*100:.0f}%)  "
              f"Pass@3: {p3_a_total}/{n} ({p3_a_total/n*100:.0f}%)")
        print(f"  Best RAG → Pass@1: {p1_b_total}/{n} ({p1_b_total/n*100:.0f}%)  "
              f"Pass@3: {p3_b_total}/{n} ({p3_b_total/n*100:.0f}%)")

    _save_incremental()  # 确保 summary 也是最新的
    print(f"\n  JSON saved: {result_path}")
    print(f"  生成可视化: python benchmark/scripts/viz_comparison.py {result_path}")


if __name__ == "__main__":
    main()

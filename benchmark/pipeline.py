"""
benchmark/pipeline.py
=====================
rag_demo 自动化评估流水线核心逻辑。

支持两种模式：
  --no-exec  — 仅评测 RAG 检索召回（快速模式）
  完整模式   — RAG 检索 + 代码生成 + 执行评测（Pass@k）

基于 phys_agent benchmark pipeline 重写，适配 rag_demo 的 GenesisAgent 架构。

典型调用：
    pipeline = BenchmarkPipeline(max_retries=3)
    results  = pipeline.run()
"""

from __future__ import annotations

import os
import sys
import json
import time
import shutil
import subprocess
import tempfile
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

# ── 确保 rag_demo 根目录在 sys.path ──────────────────────────────────────
_BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
_AGENT_ROOT    = os.path.dirname(_BENCHMARK_DIR)
_RESULTS_DIR   = os.path.join(_BENCHMARK_DIR, "results")        # results/ 根（last_result.* 固定位置）
_RUNS_DIR      = os.path.join(_RESULTS_DIR, "runs")             # results/runs/  单次运行产出
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)

from benchmark.metrics import (
    compute_rag_hit,
    compute_pass_at_k,
    get_success_attempt,
    compute_context_length,
    aggregate_metrics,
)
from benchmark.rag_adapter import rag_fast_search, retrieve_to_knowledge_list

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# 代码执行辅助
# ─────────────────────────────────────────────────────────────

def _execute_generated_code(
    code: str,
    task_id: str,
    python_exe: str = "",
    timeout: int = 600,
) -> Tuple[bool, str]:
    """
    将生成的代码写入临时文件并执行，返回 (success, output)。

    :param code: 生成的 Python 代码
    :param task_id: 任务 ID（用于临时文件命名）
    :param python_exe: Python 可执行文件路径（空则使用 sys.executable）
    :param timeout: 执行超时（秒）
    """
    exe = python_exe or sys.executable
    tmp_dir = os.path.join(_RESULTS_DIR, "tests")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"bench_{task_id}.py")

    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(code)

    env = os.environ.copy()
    env["GENESIS_OFFSCREEN"] = "1"
    env["PYTEST_VERSION"] = "1"  # 抑制一些交互式行为

    try:
        proc = subprocess.run(
            [exe, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=tmp_dir,
        )
        success = proc.returncode == 0
        output = proc.stdout + proc.stderr
        return success, output
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout}s"
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────────────────────
# 主流水线类
# ─────────────────────────────────────────────────────────────

class BenchmarkPipeline:
    """
    rag_demo 自动化评估流水线。

    :param max_retries:     每个任务最多尝试次数（用于计算 Pass@1 / Pass@3，默认 3）
    :param output_dir:      结果保存目录（默认 benchmark/results/runs/）
    :param skip_execution:  仅评测 RAG 召回，跳过代码执行（快速模式）
    :param rewrite_mode:    查询重写模式（hyde/translate/none）
    :param python_exe:      Genesis Python 可执行文件路径
    """

    def __init__(
        self,
        max_retries: int = 3,
        output_dir: Optional[str] = None,
        skip_execution: bool = False,
        rewrite_mode: str = "hyde",
        rag_hyde_route: str = "unit",
        rerank: bool = False,
        rerank_top_n: Optional[int] = None,
        python_exe: str = "",
    ):
        self.max_retries    = max_retries
        self.skip_execution = skip_execution
        self.rag_rewrite_mode = rewrite_mode
        self.rag_hyde_route = rag_hyde_route
        self.rerank         = rerank
        self.rerank_top_n   = rerank_top_n
        self.python_exe     = python_exe
        self.output_dir     = output_dir or _RUNS_DIR
        self.run_id         = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.detailed_report = False

        # RAG 检索参数（与 phys_agent benchmark pipeline 对齐）
        self.rag_search_params = {
            "rewrite_mode":    self.rag_rewrite_mode,
            "hyde_route":      self.rag_hyde_route,
            "n_api":           6,
            "n_code":          1,
            "n_snippet":       3,
            "n_error":         0,
            "n_units":         5,
            "tag_filter":      None,
            "include_core_api": True,
            "core_api_limit":  40,
            "rerank":          rerank,
            "rerank_top_n":    rerank_top_n,
            "rerank_oversample": 2.0,
        }

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(_RESULTS_DIR, exist_ok=True)

        # 懒加载
        self._agent = None
        self._rag   = None

    # ── 懒加载 ──────────────────────────────────────────────────────────────

    def _get_agent(self):
        """懒加载 GenesisAgent。"""
        if self._agent is None:
            from agent import GenesisAgent
            self._agent = GenesisAgent(
                rewrite_mode=self.rag_rewrite_mode,
                hyde_route=self.rag_hyde_route,
            )
        return self._agent

    def _get_rag(self):
        """懒加载 GenesisRAG（--no-exec 模式下直接调用 search()）。"""
        if self._rag is None:
            from rag_engine import GenesisRAG
            self._rag = GenesisRAG(reset_db=False)
        return self._rag

    # ── 主入口 ──────────────────────────────────────────────────────────────

    def run(
        self,
        query_file: Optional[str] = None,
        task_ids: Optional[List[str]] = None,
    ) -> dict:
        """
        运行完整 benchmark 流水线。

        :param query_file: benchmark JSON 路径（默认 benchmark/query.json）
        :param task_ids:   指定运行的 task_id 列表；None 表示全部
        :return: 完整结果 dict（同时保存到 output_dir）
        """
        if query_file is None:
            query_file = os.path.join(_BENCHMARK_DIR, "query.json")

        with open(query_file, "r", encoding="utf-8") as f:
            all_tasks: List[dict] = json.load(f)

        # 筛选任务
        if task_ids:
            tasks = [t for t in all_tasks if t["task_id"] in task_ids]
            if not tasks:
                raise ValueError(f"未找到指定 task_id：{task_ids}")
        else:
            tasks = all_tasks

        # 当用户指定任务子集时，自动开启详情模式
        self.detailed_report = bool(task_ids)

        self._print_header(len(tasks))

        task_results: List[dict] = []
        for i, task in enumerate(tasks):
            print(f"\n{'-'*56}")
            print(f"[{i+1:02d}/{len(tasks)}] {task['task_id']} ({task['complexity']})")
            print(f"  Query: {task['query']}")

            t0 = time.time()
            try:
                result = self._run_task(task)
            except Exception as e:
                logger.error(f"任务 {task['task_id']} 异常: {e}", exc_info=True)
                print(f"  [ERROR] task crashed: {e}")
                result = self._make_error_result(task, str(e))

            result["duration_seconds"] = round(time.time() - t0, 2)
            task_results.append(result)
            self._print_task_summary(result)

        # 汇总
        summary = aggregate_metrics(task_results)
        full_results = {
            "run_id":      self.run_id,
            "rag_rewrite_mode": self.rag_rewrite_mode,
            "rag_search_params": self.rag_search_params,
            "detailed_report": self.detailed_report,
            "max_retries": self.max_retries,
            "skip_execution": self.skip_execution,
            "timestamp":   datetime.now().isoformat(),
            "task_count":  len(tasks),
            "summary":     summary,
            "tasks":       task_results,
        }

        result_path = self._save_results(full_results)
        report_path = self._save_report(full_results)

        print(f"\n{'='*56}")
        print(f"  Benchmark 完成！")
        print(f"  JSON 结果: {result_path}")
        print(f"  文本报告: {report_path}")
        print(f"{'='*56}")
        self._print_summary(summary)

        return full_results

    # ── 任务执行 ─────────────────────────────────────────────────────────────

    def _run_task(self, task: dict) -> dict:
        """
        运行单个评测任务。

        skip_execution=True 时仅做 RAG 检索，不生成/执行代码。
        """
        expected_apis = task.get("expected_apis", [])

        # ── RAG 检索（快速模式和完整模式都走标准 search 接口）──
        rag_context = self._get_rag().search(task["query"], **self.rag_search_params)
        rag_hit = compute_rag_hit(rag_context, expected_apis)
        context_length = compute_context_length(rag_context)

        if self.skip_execution:
            # ── 快速模式：只跑 RAG ──
            out = {
                "task_id":      task["task_id"],
                "complexity":   task["complexity"],
                "query":        task["query"],
                "expected_apis": expected_apis,
                "rag_hit":      rag_hit,
                "rag_hit_after_dynamic": None,
                "rag_incremental": None,
                "execution":    None,
                "context_length_initial": context_length,
                "context_length_final": context_length,
            }
            if self.detailed_report:
                out["rag_context_initial"] = rag_context
                out["rag_context_final"] = rag_context
            return out

        # ── 完整模式：生成代码 + 执行 + 重试 ──
        agent = self._get_agent()
        attempt_results = []
        for attempt in range(1, self.max_retries + 1):
            print(f"  [Attempt {attempt}/{self.max_retries}] Generating code...")
            try:
                # 直接传入 rag_context，避免重复检索
                solve_result = agent.solve(
                    task["query"], knowledge_list=rag_context, save_code=False
                )
                code = solve_result.get("code", "")
            except Exception as e:
                print(f"  [Attempt {attempt}] Generation failed: {e}")
                attempt_results.append({
                    "attempt": attempt,
                    "success": False,
                    "error": str(e),
                    "code": "",
                })
                continue

            if not code or code.startswith("# Error"):
                print(f"  [Attempt {attempt}] Empty or error code.")
                attempt_results.append({
                    "attempt": attempt,
                    "success": False,
                    "error": "Empty code generated",
                    "code": code,
                })
                continue

            # 执行代码
            success, output = _execute_generated_code(
                code, task["task_id"], python_exe=self.python_exe,
            )
            status = "OK" if success else "FAIL"
            print(f"  [Attempt {attempt}] Execution: {status}")
            attempt_results.append({
                "attempt": attempt,
                "success": success,
                "code": code,
                "error": output if not success else None,
                "output": output[:500] if success else None,
            })

            if success:
                break

        # 执行指标
        execution = {
            "pass_at_1":      compute_pass_at_k(attempt_results, 1),
            "pass_at_3":      compute_pass_at_k(attempt_results, 3),
            "success_attempt": get_success_attempt(attempt_results),
            "total_attempts": len(attempt_results),
            "attempt_results": attempt_results,
        }

        out = {
            "task_id":       task["task_id"],
            "complexity":    task["complexity"],
            "query":         task["query"],
            "expected_apis": expected_apis,
            "rag_hit":       rag_hit,
            "rag_hit_after_dynamic": None,
            "rag_incremental": None,
            "execution":     execution,
            "context_length_initial": context_length,
            "context_length_final": context_length,
        }
        if self.detailed_report:
            out["rag_context_initial"] = rag_context
            out["rag_context_final"] = rag_context
        return out

    # ── 辅助：结果构造 ───────────────────────────────────────────────────────

    def _make_error_result(self, task: dict, error_msg: str) -> dict:
        expected_apis = task.get("expected_apis", [])
        return {
            "task_id":       task["task_id"],
            "complexity":    task["complexity"],
            "query":         task["query"],
            "expected_apis": expected_apis,
            "rag_hit": {
                "per_api":   {a: False for a in expected_apis},
                "hit_count": 0,
                "total":     len(expected_apis),
                "hit_rate":  0.0,
            },
            "execution": {
                "pass_at_1": False, "pass_at_3": False,
                "success_attempt": None, "total_attempts": 0,
                "attempt_results": [], "final_status": "error",
                "error": error_msg,
            },
            "rag_hit_after_dynamic": None,
            "rag_incremental": None,
        }

    # ── 辅助：打印 ───────────────────────────────────────────────────────────

    def _print_header(self, n: int):
        print(f"\n{'='*56}")
        print(f"  rag_demo Benchmark")
        print(f"  Run ID : {self.run_id}")
        print(f"  Tasks  : {n}")
        print(f"  RAG Rewrite: {self.rag_rewrite_mode}  |  Route: {self.rag_hyde_route}")
        print(f"  Retries: {self.max_retries}  |  Skip exec: {self.skip_execution}")
        print(f"{'='*56}")

    def _print_task_summary(self, result: dict):
        rag = result.get("rag_hit") or {}
        exe = result.get("execution")
        if rag:
            total = rag.get("total", 0)
            hit   = rag.get("hit_count", 0)
            u_hit = rag.get("unit_hit_count", 0)
            c_hit = rag.get("core_hit_count", 0)
            hit_str = (
                f"{hit}/{total} ({rag.get('hit_rate', 0)*100:.0f}%)  "
                f"[semantic={u_hit}, core={c_hit}]"
            )
        else:
            hit_str = "N/A"
        print(f"  RAG Hit : {hit_str}")
        if exe:
            p1  = "OK" if exe.get("pass_at_1") else "FAIL"
            p3  = "OK" if exe.get("pass_at_3") else "FAIL"
            att = exe.get("success_attempt") or f"--({exe.get('total_attempts', 0)} tried)"
            print(f"  Pass@1={p1}  Pass@3={p3}  (success on attempt: {att})")

    def _print_summary(self, summary: dict):
        print("\n  === 汇总 ===")
        print(
            f"  {'组别':<10} {'N':>4}  {'RAG总召回':>9}  {'语义召回':>8}  "
            f"{'TokF(avg)':>11}  {'Pass@1':>7}  {'Pass@3':>7}"
        )
        print(f"  {'-'*70}")
        for group, m in summary.items():
            n    = m.get("n", 0)
            rag  = f"{m['rag_hit_rate']*100:.1f}%"      if m.get("rag_hit_rate")      is not None else "N/A"
            urai = f"{m['unit_hit_rate']*100:.1f}%"     if m.get("unit_hit_rate")     is not None else "N/A"
            tokf = m.get("avg_context_tokens_final")
            tokf_s = f"{tokf:,.0f}" if tokf is not None else "N/A"
            p1   = f"{m['pass_at_1']*100:.1f}%"         if m.get("pass_at_1")         is not None else "N/A"
            p3   = f"{m['pass_at_3']*100:.1f}%"         if m.get("pass_at_3")         is not None else "N/A"
            print(
                f"  {group:<10} {n:>4}  {rag:>9}  {urai:>8}  "
                f"{tokf_s:>11}  {p1:>7}  {p3:>7}"
            )

    # ── 辅助：保存 ───────────────────────────────────────────────────────────

    def _save_results(self, results: dict) -> str:
        path = os.path.join(self.output_dir, f"benchmark_{self.run_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        # last_result.json 始终放在 results/ 根目录，方便 --last / 快速查看
        shutil.copy2(path, os.path.join(_RESULTS_DIR, "last_result.json"))
        return path

    def _save_report(self, results: dict) -> str:
        path = os.path.join(self.output_dir, f"benchmark_{self.run_id}_report.txt")
        lines: List[str] = []

        lines += [
            "=" * 60,
            "  rag_demo Benchmark Report",
            f"  Run ID  : {results['run_id']}",
            f"  RAG Rewrite: {results.get('rag_rewrite_mode', 'hyde')}",
            f"  RAG Search Params: {json.dumps(results.get('rag_search_params', {}), ensure_ascii=False)}",
            f"  Detailed Report: {results.get('detailed_report', False)}",
            f"  Tasks   : {results['task_count']}",
            f"  Retries : {results['max_retries']}",
            f"  Skip Exec: {results.get('skip_execution', False)}",
            f"  Time    : {results['timestamp']}",
            "=" * 60,
            "",
        ]

        # 汇总表
        lines.append("--- 汇总指标 ---")
        lines.append(
            f"{'组别':<12} {'N':>4}  {'RAG总召回':>9}  {'语义召回':>8}  "
            f"{'TokF(avg)':>10}  {'Pass@1':>7}  {'Pass@3':>7}"
        )
        lines.append("-" * 68)
        for group, m in results["summary"].items():
            n    = m.get("n", 0)
            rag  = f"{m['rag_hit_rate']*100:.1f}%"      if m.get("rag_hit_rate")  is not None else "N/A"
            urai = f"{m['unit_hit_rate']*100:.1f}%"     if m.get("unit_hit_rate") is not None else "N/A"
            tokf = m.get("avg_context_tokens_final")
            tokf_s = f"{tokf:,.0f}" if tokf is not None else "N/A"
            p1   = f"{m['pass_at_1']*100:.1f}%"         if m.get("pass_at_1")     is not None else "N/A"
            p3   = f"{m['pass_at_3']*100:.1f}%"         if m.get("pass_at_3")     is not None else "N/A"
            lines.append(
                f"{group:<12} {n:>4}  {rag:>9}  {urai:>8}  "
                f"{tokf_s:>10}  {p1:>7}  {p3:>7}"
            )
        lines.append("")

        # 逐任务详情
        lines.append("--- 逐任务结果 ---")
        lines.append(f"{'task_id':<12} {'cx':>6}  {'RAG':>6}  {'TokI/F':>11}  {'P@1':>4}  {'P@3':>4}  {'att':>4}  {'sec':>7}")
        lines.append("-" * 60)
        for r in results["tasks"]:
            rag_r = r.get("rag_hit") or {}
            exe   = r.get("execution") or {}
            rag_s = f"{rag_r.get('hit_rate', 0)*100:.0f}%" if rag_r else "N/A"
            p1    = "OK" if exe.get("pass_at_1") else ("FAIL" if r.get("execution") is not None else "-")
            p3    = "OK" if exe.get("pass_at_3") else ("FAIL" if r.get("execution") is not None else "-")
            att   = str(exe.get("success_attempt") or "-")
            sec   = f"{r.get('duration_seconds', '-')}s"
            tok_i = (r.get("context_length_initial") or {}).get("total_tokens")
            tok_f = (r.get("context_length_final") or {}).get("total_tokens")
            tok_i_s = f"{tok_i:,}" if isinstance(tok_i, (int, float)) else "-"
            eff_f = tok_f if isinstance(tok_f, (int, float)) else tok_i
            tok_f_s = f"{eff_f:,}" if isinstance(eff_f, (int, float)) else "-"
            tok_cell = f"{tok_i_s}/{tok_f_s}"
            lines.append(
                f"{r['task_id']:<12} {r['complexity']:>6}  {rag_s:>6}  {tok_cell:>11}  {p1:>4}  {p3:>4}  {att:>4}  {sec:>7}"
            )

        # RAG 命中详情（per-task per-api）
        lines += ["", "--- RAG 命中详情（per API）---"]
        for r in results["tasks"]:
            rag_r = r.get("rag_hit") or {}
            per_api = rag_r.get("per_api", {})
            if not per_api:
                continue
            lines.append(f"\n  {r['task_id']}:")
            for api, info in per_api.items():
                if isinstance(info, dict):
                    hit = bool(info.get("hit", False))
                    source = info.get("source", "miss")
                else:
                    hit = bool(info)
                    source = "unknown"
                mark = "Y" if hit else "N"
                lines.append(f"    {mark} {api}  [{source}]")

        # 详情模式：输出每个任务的完整 RAG 检索内容
        if results.get("detailed_report", False):
            lines += ["", "--- 详细检索内容（完整上下文）---"]
            for r in results["tasks"]:
                lines.append("")
                lines.append(f"  [{r['task_id']}] query: {r.get('query', '')}")
                lines.append("  - RAG Context:")
                ctx = r.get("rag_context_initial", []) or []
                if not ctx:
                    lines.append("    (empty)")
                for idx, item in enumerate(ctx, 1):
                    if not isinstance(item, dict):
                        lines.append(f"    [{idx}] {str(item)}")
                        continue
                    itype = item.get("type", "")
                    meta = item.get("meta", {}) or {}
                    content = item.get("content", "")
                    lines.append(f"    [{idx}] type={itype}  meta={json.dumps(meta, ensure_ascii=False)}")
                    lines.append("    ----- content begin -----")
                    lines.append(str(content))
                    lines.append("    ----- content end -----")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        shutil.copy2(path, os.path.join(_RESULTS_DIR, "last_result.txt"))
        return path

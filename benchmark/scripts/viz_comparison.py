#!/usr/bin/env python3
"""
为 RAG vs No-RAG 对比实验结果生成可视化 HTML。

对比实验的 result.json 格式与标准 benchmark 不同（按条件分组而非按复杂度），
本脚本把它转换成两个标准格式的 run（no_rag + best_rag），复用 viz_report.build_html，
从而得到「和正常 result 完全一样」的可视化（对比柱状图 + 逐任务热力图 + 分难度统计）。

用法：
  cd rag_demo/
  python benchmark/scripts/viz_comparison.py [comparison_result.json] [-o output.html]

默认输入：benchmark/results/comparisons/rag_vs_no_rag/result.json
默认输出：同目录下的 report.html
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
_BENCH_DIR = os.path.join(_ROOT, "benchmark")

from benchmark.metrics import aggregate_metrics
from benchmark.viz_report import build_html


def _load_query_map() -> Dict[str, str]:
    """从 query.json 读取 task_id → query 映射，用于补全表格里的 query 列。"""
    qpath = os.path.join(_BENCH_DIR, "query.json")
    if not os.path.isfile(qpath):
        return {}
    try:
        tasks = json.load(open(qpath, encoding="utf-8"))
        return {t["task_id"]: t.get("query", "") for t in tasks}
    except Exception:
        return {}


def _conv_task(ct: Dict[str, Any], qmap: Dict[str, str]) -> Dict[str, Any]:
    """
    把对比实验的单个任务转成标准 benchmark 任务格式。

    对比任务字段：task_id, complexity, pass_at_1, pass_at_3, success_attempt,
                 total_attempts, attempts[], duration
    标准任务需要：task_id, complexity, query, execution{...}, rag_hit(可选),
                 context_length_final(可选), duration_seconds
    """
    tid = ct.get("task_id", "")
    exe = ct.get("attempts")  # 有 attempts 说明是执行对比
    standard: Dict[str, Any] = {
        "task_id": tid,
        "complexity": ct.get("complexity", "unknown"),
        "query": ct.get("query") or qmap.get(tid, ""),
        "duration_seconds": ct.get("duration") or ct.get("duration_seconds"),
    }

    # 执行数据（对比实验的主要指标）
    if ct.get("pass_at_1") is not None or ct.get("pass_at_3") is not None or exe:
        standard["execution"] = {
            "pass_at_1": ct.get("pass_at_1"),
            "pass_at_3": ct.get("pass_at_3"),
            "success_attempt": ct.get("success_attempt"),
            "total_attempts": ct.get("total_attempts", len(exe) if exe else 0),
        }

    # RAG 命中数据（no-exec 对比实验会有；执行对比没有则留空）
    if ct.get("rag_hit"):
        standard["rag_hit"] = ct["rag_hit"]
    if ct.get("context_length_final"):
        standard["context_length_final"] = ct["context_length_final"]
        standard["context_length_initial"] = ct.get("context_length_initial", ct["context_length_final"])

    return standard


def _build_run(
    label: str,
    cond_tasks: List[Dict[str, Any]],
    comp_meta: Dict[str, Any],
    qmap: Dict[str, str],
    condition_key: str,
) -> Tuple[str, Dict[str, Any]]:
    """把一个条件的任务列表转成标准 run dict。"""
    standard_tasks = [_conv_task(t, qmap) for t in cond_tasks]
    summary = aggregate_metrics(standard_tasks)

    is_rag = condition_key == "best_rag"
    model = comp_meta.get("model", "")
    params = comp_meta.get("best_rag_params", {}) if is_rag else {}

    run = {
        "run_id": f"{condition_key}_{comp_meta.get('timestamp', '')}",
        "timestamp": comp_meta.get("timestamp", ""),
        "rag_rewrite_mode": params.get("rewrite_mode", "none") if is_rag else "none",
        "rag_search_params": params if is_rag else {"rerank": False},
        "skip_execution": all(t.get("execution") is None for t in standard_tasks),
        "max_retries": comp_meta.get("max_retries", 3),
        "task_count": len(standard_tasks),
        "summary": summary,
        "tasks": standard_tasks,
        "model": model,
        "condition": condition_key,
    }
    return label, run


def main():
    ap = argparse.ArgumentParser(description="为对比实验结果生成可视化 HTML")
    ap.add_argument(
        "input", nargs="?", default=None,
        help="对比实验 result.json（默认 benchmark/results/comparisons/rag_vs_no_rag/result.json）",
    )
    ap.add_argument("-o", "--output", default=None, help="HTML 输出路径")
    ap.add_argument("--title", default=None, help="报告标题")
    args = ap.parse_args()

    # 默认输入
    inp = args.input or os.path.join(_BENCH_DIR, "results", "comparisons", "rag_vs_no_rag", "result.json")
    if not os.path.isfile(inp):
        # 兜底：在 comparisons/ 下找最新的 result.json
        comp_dir = os.path.join(_BENCH_DIR, "results", "comparisons")
        cands = sorted(Path(comp_dir).rglob("result.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not cands:
            print(f"未找到对比实验结果：{inp}", file=sys.stderr)
            sys.exit(1)
        inp = str(cands[0])
        print(f"自动选择最新结果：{inp}")

    d = json.load(open(inp, encoding="utf-8"))
    tasks_by_cond = d.get("tasks", {})
    if not isinstance(tasks_by_cond, dict):
        print("结果文件不是对比实验格式（缺少 tasks.no_rag / tasks.best_rag）", file=sys.stderr)
        sys.exit(1)

    qmap = _load_query_map()
    comp_meta = {
        "model": d.get("model", ""),
        "timestamp": d.get("timestamp", ""),
        "best_rag_params": d.get("best_rag_params", {}),
        "max_retries": d.get("max_retries", 3),
    }

    # 决定要渲染哪些条件（按出现顺序）
    cond_labels = {
        "no_rag": "No RAG",
        "best_rag": "Best RAG",
    }
    runs = []
    for key in ["no_rag", "best_rag"]:
        if key in tasks_by_cond and tasks_by_cond[key]:
            runs.append(_build_run(cond_labels[key], tasks_by_cond[key], comp_meta, qmap, key))

    if not runs:
        print("结果文件中没有可渲染的条件数据", file=sys.stderr)
        sys.exit(1)

    model_str = f" ({comp_meta['model']})" if comp_meta["model"] else ""
    title = args.title or f"RAG vs No-RAG 对比{model_str}"

    # build_html 接收 (label, json_path_or_none, data_dict)
    runs_for_html = [(label, None, run) for label, run in runs]
    html = build_html(runs_for_html, title=title)

    out = args.output or str(Path(inp).parent / "report.html")
    Path(out).resolve().parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(html, encoding="utf-8")
    print(f"可视化报告已生成：{out}")
    print(f"  实验数：{len(runs)}")
    for label, run in runs:
        o = run["summary"].get("overall", {})
        p1 = o.get("pass_at_1")
        p3 = o.get("pass_at_3")
        rag = o.get("rag_hit_rate")
        print(f"  - {label}: N={run['task_count']}  "
              f"P@1={f'{p1*100:.0f}%' if isinstance(p1,(int,float)) else '—'}  "
              f"P@3={f'{p3*100:.0f}%' if isinstance(p3,(int,float)) else '—'}  "
              f"RAG={f'{rag*100:.0f}%' if isinstance(rag,(int,float)) else '—'}")


if __name__ == "__main__":
    main()

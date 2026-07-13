#!/usr/bin/env python3
"""
rag_demo 自动化评估流水线入口
==============================

用法（在 rag_demo/ 目录下运行）：

  # 全量评测（最多 3 次尝试）
  python benchmark/run_benchmark.py

  # 仅评测 RAG 召回（跳过代码执行，速度快）
  python benchmark/run_benchmark.py --no-exec

  # 指定任务子集
  python benchmark/run_benchmark.py --tasks eval_001,eval_002,eval_003
  # 指定任务子集时，会自动开启详细报告（输出完整 RAG 检索内容）

  # 调整重试次数
  python benchmark/run_benchmark.py --max-retries 1

  # 指定 Genesis Python
  python benchmark/run_benchmark.py --python /path/to/genesis_python

  # 控制 RAG 查询重写模式
  python benchmark/run_benchmark.py --rewrite-mode none

  # 运行后生成 HTML 可视化
  python benchmark/run_benchmark.py --no-exec --viz

评测指标：
  - RAG 召回率   : 初始检索结果是否覆盖 expected_apis
  - Pass@1       : 第 1 次生成的代码是否直接执行成功
  - Pass@3       : 3 次尝试内是否执行成功
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# 确保 rag_demo 根目录在 sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from benchmark.pipeline import BenchmarkPipeline


def _run_miss_audit(result_json: str) -> None:
    """调用 miss API 审查脚本；失败不阻断 benchmark 主流程。"""
    script = Path(__file__).resolve().parent / "scripts" / "analyze_benchmark_miss_kb.py"
    if not script.is_file():
        print(f"未找到 miss 审查脚本，跳过: {script}", file=sys.stderr)
        return
    cmd = [sys.executable, str(script), "--result-json", result_json]
    print(f"自动执行 miss 审查: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=Path(__file__).resolve().parent)
    if proc.returncode != 0:
        print(f"miss 审查失败（exit={proc.returncode}），已跳过", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="rag_demo 自动化 benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--tasks",
        type=str,
        default=None,
        metavar="ID1,ID2,...",
        help="指定运行的 task_id（逗号分隔）；默认全量运行。指定后自动开启详细报告",
    )
    p.add_argument(
        "--max-retries",
        type=int,
        default=3,
        metavar="K",
        help="每个任务最多尝试次数（默认 3，对应 Pass@1/Pass@3）",
    )
    p.add_argument(
        "--output-dir",
        type=str,
        default=None,
        metavar="DIR",
        help="结果保存目录（默认 benchmark/results/runs/）",
    )
    p.add_argument(
        "--query-file",
        type=str,
        default=None,
        metavar="FILE",
        help="benchmark JSON 文件路径（默认 benchmark/query.json）",
    )
    p.add_argument(
        "--no-exec",
        action="store_true",
        help="跳过代码执行，仅评测 RAG 召回率（快速模式）",
    )
    p.add_argument(
        "--rewrite-mode",
        choices=["hyde", "translate", "none"],
        default="hyde",
        dest="rewrite_mode",
        help="RAG 查询重写模式（默认 hyde）",
    )
    p.add_argument(
        "--rag-hyde-route",
        choices=["unit", "fourway"],
        default="unit",
        dest="rag_hyde_route",
        help="hyde 模式下的检索路由（unit=知识单元, fourway=四路检索，默认 unit）",
    )
    p.add_argument(
        "--rerank",
        action="store_true",
        help="启用 reranker 重排序（当前 rag_demo 暂未实现，保留参数）",
    )
    p.add_argument(
        "--rerank-top-n",
        type=int,
        default=None,
        metavar="N",
        help="rerank 后保留的语义条数（默认不截断）",
    )
    p.add_argument(
        "--python",
        type=str,
        default="",
        metavar="EXE",
        help="Genesis Python 可执行文件路径（默认使用当前 Python）",
    )
    p.add_argument(
        "--viz",
        action="store_true",
        help="运行结束后生成交互式 HTML 可视化报告（Chart.js 单文件）",
    )
    p.add_argument(
        "--viz-output",
        type=str,
        default=None,
        metavar="FILE.html",
        help="可视化 HTML 输出路径（默认：<结果目录>/benchmark_viz.html）",
    )
    return p.parse_args()


def main():
    args = parse_args()

    task_ids = None
    if args.tasks:
        task_ids = [t.strip() for t in args.tasks.split(",") if t.strip()]

    pipeline = BenchmarkPipeline(
        max_retries=args.max_retries,
        output_dir=args.output_dir,
        skip_execution=args.no_exec,
        rewrite_mode=args.rewrite_mode,
        rag_hyde_route=args.rag_hyde_route,
        rerank=args.rerank,
        rerank_top_n=args.rerank_top_n,
        python_exe=args.python,
    )

    results = pipeline.run(
        query_file=args.query_file,
        task_ids=task_ids,
    )
    run_id = results.get("run_id")
    result_json = Path(pipeline.output_dir) / f"benchmark_{run_id}.json"
    if result_json.is_file():
        _run_miss_audit(str(result_json))
    else:
        print(f"未找到结果 JSON，跳过 miss 审查: {result_json}", file=sys.stderr)

    if args.viz:
        bench_dir = Path(__file__).resolve().parent
        results_dir = Path(args.output_dir) if args.output_dir else bench_dir / "results"
        candidates = sorted(
            results_dir.rglob("benchmark_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        # 排除 miss 审查产生的侧边文件
        candidates = [c for c in candidates if "benchmark_miss_" not in c.name]
        if not candidates:
            print("未找到 benchmark_*.json，跳过 --viz", file=sys.stderr)
        else:
            from benchmark.viz_report import write_benchmark_html

            out_html = args.viz_output or str(results_dir / "benchmark_viz.html")
            path = write_benchmark_html([str(candidates[0])], output_path=out_html)
            print(f"可视化报告: {path}")


if __name__ == "__main__":
    main()

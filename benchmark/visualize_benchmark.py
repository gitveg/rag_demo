#!/usr/bin/env python3
"""
将 benchmark JSON 渲染为单页 HTML 报告（交互图表 + 表格）。

用法（在 rag_demo 目录下）：

  # 单次结果（默认写到同目录 benchmark_viz.html）
  python benchmark/visualize_benchmark.py benchmark/results/runs/benchmark_20260101_120000.json

  # 指定输出路径
  python benchmark/visualize_benchmark.py -o report.html results/last_result.json

  # 多次对比（多文件 = 多曲线 / 热力表）
  python visualize_benchmark.py run_a/benchmark_*.json   # 需 shell 展开

  # 使用 batch 生成的 manifest
  python benchmark/visualize_benchmark.py --manifest benchmark/results/batch/20260109_120000/manifest.json

  # 最近一次 run_benchmark 写入的 last_result.json
  python benchmark/visualize_benchmark.py --last

也可由 run_benchmark.py --viz 或 run_benchmark_batch.py 自动调用。
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path

_BENCH_DIR = Path(__file__).resolve().parent
_AGENT_ROOT = _BENCH_DIR.parent
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))

from benchmark.viz_report import load_manifest, write_benchmark_html  # noqa: E402


def _default_last_json() -> Path:
    return _BENCH_DIR / "results" / "last_result.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="Benchmark 结果可视化（HTML）")
    ap.add_argument(
        "paths",
        nargs="*",
        help="benchmark_*.json 路径（可多个）；与 --manifest / --last 互斥时可省略",
    )
    ap.add_argument(
        "-o",
        "--output",
        default=None,
        help="输出 HTML 路径（默认：单文件时与 JSON 同目录的 benchmark_viz.html；多文件时 ./benchmark_compare.html）",
    )
    ap.add_argument(
        "--manifest",
        metavar="FILE",
        help="batch 生成的 manifest.json（内含各子实验 result json 路径）",
    )
    ap.add_argument(
        "--last",
        action="store_true",
        help=f"使用 {_default_last_json()}",
    )
    ap.add_argument("--title", default=None, help="报告标题")
    args = ap.parse_args()

    json_paths: list[str] = []

    if args.manifest:
        json_paths = load_manifest(args.manifest)
        if not json_paths:
            print("manifest 中无有效 json 路径", file=sys.stderr)
            return 1
    elif args.last:
        lp = _default_last_json()
        if not lp.is_file():
            print(f"未找到 {lp}", file=sys.stderr)
            return 1
        json_paths = [str(lp)]
    elif args.paths:
        for pattern in args.paths:
            if any(c in pattern for c in "*?[]"):
                json_paths.extend(sorted(glob.glob(pattern)))
            else:
                p = Path(pattern)
                if not p.is_file():
                    print(f"文件不存在: {pattern}", file=sys.stderr)
                    return 1
                json_paths.append(str(p.resolve()))
    else:
        ap.print_help()
        print("\n请提供 json 路径、--manifest 或 --last", file=sys.stderr)
        return 1

    # 去重且保持顺序
    seen = set()
    unique: list[str] = []
    for p in json_paths:
        rp = str(Path(p).resolve())
        if rp not in seen:
            seen.add(rp)
            unique.append(rp)

    out = args.output
    if out is None:
        if len(unique) == 1:
            out = str(Path(unique[0]).parent / "benchmark_viz.html")
        else:
            out = str(_BENCH_DIR / "benchmark_compare.html")

    try:
        written = write_benchmark_html(unique, output_path=out, title=args.title)
    except Exception as e:
        print(f"生成失败: {e}", file=sys.stderr)
        return 1

    print(f"已生成: {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

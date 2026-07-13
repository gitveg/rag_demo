"""
Batch runner for rag_demo benchmark commands.

Usage:
    python benchmark/run_benchmark_batch.py
    python benchmark/run_benchmark_batch.py --no-subdirs   # 不注入独立 output-dir
    python benchmark/run_benchmark_batch.py --no-viz       # 不自动生成对比 HTML

Edit `COMMANDS` below to add/remove benchmark runs.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

# 同 project 下 benchmark 包
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from benchmark.viz_report import pick_main_benchmark_json  # noqa: E402


# 实验配置：每条命令会自动注入独立 --output-dir
COMMANDS: List[List[str]] = [
    # ── baseline 组（与 phys_agent 实验矩阵对齐）──
    ["run_benchmark.py", "--no-exec", "--rewrite-mode", "none"],                                        # ① 四路 baseline（none → fourway）
    ["run_benchmark.py", "--no-exec"],                                                                  # ② HyDE + unit（默认）
    ["run_benchmark.py", "--no-exec", "--rewrite-mode", "hyde", "--rag-hyde-route", "fourway"],        # ③ HyDE + fourway
]


def _has_output_dir(cmd_args: List[str]) -> bool:
    return "--output-dir" in cmd_args


def _run_miss_audit(workdir: Path, result_json: str) -> None:
    """对子实验结果执行 miss API 审查；失败不阻断 batch。"""
    script = workdir / "scripts" / "analyze_benchmark_miss_kb.py"
    if not script.is_file():
        print(f"未找到 miss 审查脚本，跳过: {script}", file=sys.stderr)
        return
    cmd = [sys.executable, str(script), "--result-json", result_json]
    print(f"  -> 自动执行 miss 审查: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=workdir)
    if proc.returncode != 0:
        print(f"  -> miss 审查失败（exit={proc.returncode}），已跳过", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="批量运行 run_benchmark 子实验")
    ap.add_argument(
        "--no-subdirs",
        action="store_true",
        help="不向每条命令注入 --output-dir（多轮会互相覆盖 last_result.json，不利于对比）",
    )
    ap.add_argument(
        "--no-viz",
        action="store_true",
        help="batch 结束后不自动调用 visualize_benchmark 生成对比 HTML",
    )
    args = ap.parse_args()

    workdir = Path(__file__).resolve().parent
    print(f"Working directory: {workdir}")
    print(f"Total commands: {len(COMMANDS)}")

    batch_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_root = workdir / "results" / "batch" / batch_stamp
    if not args.no_subdirs:
        batch_root.mkdir(parents=True, exist_ok=True)

    manifest: List[dict] = []
    fail_count = 0

    for idx, cmd_args in enumerate(COMMANDS, start=1):
        cmd_list = list(cmd_args)
        run_dir: Path | None = None
        if not args.no_subdirs and not _has_output_dir(cmd_list):
            run_dir = batch_root / f"run_{idx:02d}"
            run_dir.mkdir(parents=True, exist_ok=True)
            cmd_list = cmd_list + ["--output-dir", str(run_dir)]

        full_cmd = [sys.executable, *cmd_list]
        cmd_show = " ".join(full_cmd)
        print("\n" + "=" * 80)
        print(f"[{idx}/{len(COMMANDS)}] Running: {cmd_show}")
        print("=" * 80)

        start = time.time()
        proc = subprocess.run(full_cmd, cwd=workdir)
        elapsed = time.time() - start

        ok = proc.returncode == 0
        if not ok:
            fail_count += 1
        status = "OK" if ok else "FAIL"
        print(f"[{idx}/{len(COMMANDS)}] {status} (exit={proc.returncode}, {elapsed:.1f}s)")

        json_path: str | None = None
        if run_dir is not None:
            main = pick_main_benchmark_json(run_dir)
            if main is not None:
                json_path = str(main.resolve())
        elif not args.no_subdirs:
            pass
        else:
            res = workdir / "results" / "runs"
            main = pick_main_benchmark_json(res)
            if main is not None:
                json_path = str(main.resolve())

        manifest.append(
            {
                "index": idx,
                "command": cmd_show,
                "returncode": proc.returncode,
                "elapsed_sec": round(elapsed, 1),
                "output_dir": str(run_dir.resolve()) if run_dir else None,
                "json": json_path,
            }
        )

    manifest_path: Path | None = None
    if not args.no_subdirs:
        manifest_path = batch_root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nBatch manifest: {manifest_path}")

    print("\n" + "#" * 80)
    print("Batch summary")
    print("#" * 80)
    for r in manifest:
        ok = r["returncode"] == 0
        status = "OK  " if ok else "FAIL"
        print(f'{status}  [{r["index"]}] {r["command"]} ({r["elapsed_sec"]}s)')

    print("-" * 80)
    print(f"Done. Success: {len(manifest) - fail_count}, Failed: {fail_count}")

    if not args.no_viz and manifest_path and manifest_path.is_file():
        json_paths = [m["json"] for m in manifest if m.get("json")]
        if len(json_paths) >= 1:
            viz_py = workdir / "visualize_benchmark.py"
            out_html = batch_root / "batch_report.html"
            vcmd = [
                sys.executable,
                str(viz_py),
                "--manifest",
                str(manifest_path),
                "-o",
                str(out_html),
                "--title",
                f"Batch {batch_stamp}",
            ]
            print(f"\nGenerating visualization: {' '.join(vcmd)}")
            vr = subprocess.run(vcmd, cwd=workdir.parent)
            if vr.returncode == 0:
                print(f"可视化报告: {out_html}")
        else:
            print("\n跳过可视化：未找到任何 benchmark_*.json（子实验可能全部失败）")

    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())

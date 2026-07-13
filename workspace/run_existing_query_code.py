from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from feedback_loop.run_and_collect import execute_code


def load_prompts(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("prompts", [])


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts", default="benchmark/query.json")
    parser.add_argument("--code-dir", default="workspace/feedback_build")
    parser.add_argument("--fallback-code-dir", default="workspace/constraint_build")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--max-prompts", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--log", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    prompts = load_prompts(ROOT / args.prompts)
    prompts = prompts[max(args.start_index, 0):]
    if args.max_prompts > 0:
        prompts = prompts[:args.max_prompts]

    code_dir = ROOT / args.code_dir
    fallback_code_dir = ROOT / args.fallback_code_dir if args.fallback_code_dir else None
    log_path = ROOT / args.log
    if args.overwrite and log_path.exists():
        log_path.unlink()

    total = len(prompts)
    ok = 0
    fail = 0
    missing = 0
    started = time.time()

    print(f"Executing existing query code: {total} prompts")
    print(f"Code dir: {code_dir}")
    if fallback_code_dir:
        print(f"Fallback code dir: {fallback_code_dir}")
    print(f"Log: {log_path}")

    for i, item in enumerate(prompts, 1):
        task_id = item.get("task_id", f"task_{i:03d}")
        query = item.get("query", "")
        code_path = code_dir / f"{task_id}.py"
        if not code_path.exists() and fallback_code_dir:
            fallback_path = fallback_code_dir / f"{task_id}.py"
            if fallback_path.exists():
                code_path = fallback_path
        print(f"[{i}/{total}] {task_id}")

        if not code_path.exists():
            missing += 1
            result = {
                "success": False,
                "error_type": "MissingCode",
                "concise_error": f"Missing generated code: {code_path}",
                "stdout": "",
                "stderr": f"Missing generated code: {code_path}",
                "execution_analysis": {"returncode": None, "phase_summary": []},
            }
            elapsed = 0.0
        else:
            t0 = time.time()
            result = execute_code(str(code_path), timeout=args.timeout)
            elapsed = time.time() - t0

        success = result.get("success") is True
        ok += int(success)
        fail += int(not success)

        record = {
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "task_id": task_id,
            "query": query,
            "code_path": str(code_path),
            "attempt": 1,
            "success": success,
            "error_type": result.get("error_type", ""),
            "concise_error": (result.get("concise_error", "") or "")[:8000],
            "stderr": (result.get("stderr", "") or "")[:2000],
            "stdout": (result.get("stdout", "") or "")[:500],
            "execution_analysis": result.get("execution_analysis", {}),
            "gen_elapsed_sec": 0.0,
            "exec_elapsed_sec": round(elapsed, 1),
            "key_apis": [],
            "knowledge_ids": [],
            "rewrite_mode": "existing_constraint_build",
        }
        append_jsonl(log_path, record)

    elapsed_total = time.time() - started
    print(f"Done: total={total} ok={ok} fail={fail} missing={missing} elapsed={elapsed_total:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

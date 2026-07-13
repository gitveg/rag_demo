"""Run a guarded fresh online benchmark and process Loop B/C candidates."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAG_DEMO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, RAG_DEMO_ROOT)

from event_schema import make_run_id, sanitize_task_id
from processor import run as process_feedback
from run_and_collect import DEFAULT_PROMPTS, run as collect_run
from utils import load_jsonl, save_json


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _stats(log_path: str) -> dict:
    records = load_jsonl(log_path)
    return {
        "records": len(records),
        "generation_failed": sum(r.get("outcome") == "generation_failed" for r in records),
        "process_passed": sum(r.get("outcome") == "process_passed" for r in records),
        "execution_failed": sum(
            r.get("stage") == "execution" and r.get("success") is False for r in records
        ),
    }


def _write_state(path: str, state: dict, **updates) -> None:
    state.update(updates)
    state["updated_at"] = _now()
    save_json(path, state)


def _load_prompt_count(path: str) -> int:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    prompts = data if isinstance(data, list) else data.get("prompts", [])
    return len(prompts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Guarded fresh online run for all benchmark prompts")
    parser.add_argument("--prompts", default=DEFAULT_PROMPTS)
    parser.add_argument("--log", default="")
    parser.add_argument("--state", default="")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--timeout", type=int, default=150)
    parser.add_argument("--rewrite-mode", choices=["none", "translate", "hyde"], default="hyde")
    args = parser.parse_args()

    run_id = sanitize_task_id(args.run_id, fallback=make_run_id()) if args.run_id else make_run_id()
    log_dir = os.path.join(RAG_DEMO_ROOT, "workspace", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = args.log or os.path.join(log_dir, f"execution_log_online_{run_id}.jsonl")
    state_path = args.state or os.path.join(log_dir, f"online_run_{run_id}_state.json")
    expected = _load_prompt_count(args.prompts)

    if os.path.exists(log_path):
        raise FileExistsError(f"Refusing to append a fresh run to existing log: {log_path}")

    state = {
        "schema_version": 1,
        "pid": os.getpid(),
        "run_id": run_id,
        "prompts": os.path.abspath(args.prompts),
        "expected_records": expected,
        "log": os.path.abspath(log_path),
        "state_file": os.path.abspath(state_path),
        "started_at": _now(),
    }
    _write_state(state_path, state, status="preflight_running", stats=_stats(log_path))

    try:
        collect_run(
            prompts_file=args.prompts,
            log_path=log_path,
            max_prompts=1,
            start_index=0,
            rewrite_mode=args.rewrite_mode,
            timeout=args.timeout,
            auto_process=False,
            run_id=run_id,
        )
        records = load_jsonl(log_path)
        if len(records) != 1 or records[0].get("stage") != "execution":
            reason = records[0].get("concise_error", "preflight did not produce an execution event") if records else "preflight produced no event"
            _write_state(
                state_path,
                state,
                status="preflight_failed",
                failure_reason=reason[:2000],
                stats=_stats(log_path),
            )
            return 2

        _write_state(state_path, state, status="full_run_running", stats=_stats(log_path))
        if expected > 1:
            collect_run(
                prompts_file=args.prompts,
                log_path=log_path,
                max_prompts=0,
                start_index=1,
                rewrite_mode=args.rewrite_mode,
                timeout=args.timeout,
                auto_process=False,
                run_id=run_id,
            )

        stats = _stats(log_path)
        if stats["records"] != expected:
            _write_state(
                state_path,
                state,
                status="incomplete",
                failure_reason=f"expected {expected} records, found {stats['records']}",
                stats=stats,
            )
            return 3

        _write_state(state_path, state, status="processing_feedback", stats=stats)
        process_feedback(log_path, loops="bc", dry_run=False)
        _write_state(state_path, state, status="complete", stats=_stats(log_path), completed_at=_now())
        return 0
    except Exception as exc:
        _write_state(
            state_path,
            state,
            status="failed",
            failure_reason=f"{type(exc).__name__}: {exc}"[:2000],
            stats=_stats(log_path),
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())

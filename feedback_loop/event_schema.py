"""Stable identifiers and validation helpers for feedback execution events."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import re
import sys
import uuid
from datetime import datetime
from typing import Any, Mapping


SCHEMA_VERSION = 2
_TASK_ID_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def sha256_text(value: str) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def sanitize_task_id(value: str, fallback: str = "task") -> str:
    """Return a path-safe task id while preserving common benchmark ids."""
    cleaned = _TASK_ID_RE.sub("_", str(value or "")).strip("._-")
    cleaned = cleaned[:120]
    return cleaned or fallback


def make_run_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"run_{stamp}_{uuid.uuid4().hex[:8]}"


def environment_fingerprint() -> dict:
    genesis_version = "unknown"
    for distribution in ("genesis-world", "genesis"):
        try:
            genesis_version = importlib.metadata.version(distribution)
            break
        except importlib.metadata.PackageNotFoundError:
            continue
    return {
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "genesis_version": genesis_version,
        "backend": os.getenv("GENESIS_BACKEND", "unspecified"),
        "offscreen": os.getenv("GENESIS_OFFSCREEN", "1"),
    }


def make_event_id(
    run_id: str,
    task_id: str,
    prompt_index: int,
    attempt: int,
    stage: str,
    code_sha256: str = "",
) -> str:
    payload = {
        "run_id": run_id,
        "task_id": task_id,
        "prompt_index": int(prompt_index),
        "attempt": int(attempt),
        "stage": stage,
        "code_sha256": code_sha256,
    }
    digest = sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return f"evt_{digest}"


def record_event_id(record: Mapping[str, Any]) -> str:
    """Return an explicit v2 event id or a deterministic id for a legacy record."""
    explicit = str(record.get("event_id", "")).strip()
    if explicit:
        return explicit

    legacy_payload = {
        "timestamp": record.get("timestamp"),
        "task_id": record.get("task_id"),
        "query": record.get("query"),
        "code_path": record.get("code_path"),
        "attempt": record.get("attempt", 1),
        "success": record.get("success"),
        "error_type": record.get("error_type"),
        "concise_error": record.get("concise_error"),
    }
    digest = sha256_text(json.dumps(legacy_payload, ensure_ascii=False, sort_keys=True, default=str))
    return f"legacy_evt_{digest}"


def validate_execution_record(record: Mapping[str, Any]) -> list[str]:
    """Validate the minimum contract needed by the feedback processor."""
    errors = []
    for key in ("task_id", "query", "attempt", "success"):
        if key not in record:
            errors.append(f"missing field: {key}")
    if "success" in record and not isinstance(record.get("success"), bool):
        errors.append("success must be boolean")
    if record.get("schema_version", 1) >= 2:
        for key in ("event_id", "run_id", "prompt_index", "outcome"):
            if key not in record:
                errors.append(f"missing v2 field: {key}")
    return errors

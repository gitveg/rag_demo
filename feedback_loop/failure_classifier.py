"""Deterministic first-pass classification for execution failures."""

from __future__ import annotations

from typing import Mapping, Tuple


NON_KNOWLEDGE_CATEGORIES = frozenset({
    "generation",
    "dependency",
    "resource",
    "timeout",
    "infrastructure",
    "engine_internal",
    "syntax",
})


def classify_failure(error_type: str, text: str) -> str:
    combined = f"{error_type or ''}\n{text or ''}".lower()

    if "timeouterror" in combined or "timeoutexpired" in combined or "timeout after" in combined:
        return "timeout"
    if any(token in combined for token in (
        "modulenotfounderror", "no module named", "importerror", "dll load failed",
    )):
        return "dependency"
    if any(token in combined for token in (
        "virtual memory allocation", "out of memory", "cuda_error_out_of_memory",
        "memoryerror", "cannot allocate memory", "std::bad_alloc",
    )):
        return "resource"
    if any(token in combined for token in (
        "cuda_error_illegal_address", "device-side assert triggered",
        "host_memory_pool.cpp", "driver shutting down",
    )):
        return "engine_internal"
    if "syntaxerror" in combined or "indentationerror" in combined:
        return "syntax"
    if "filenotfounderror" in combined or "no such file or directory" in combined:
        return "asset_path"
    if any(token in combined for token in (
        "unexpected keyword argument", "unrecognized attribute", "missing required",
        "got multiple values for argument", "takes " , "object has no attribute",
        "scene is already built", "must be called before", "must be called after",
    )):
        return "api_usage"
    if any(token in combined for token in ("connection error", "invalid_api_key", "rate limit")):
        return "infrastructure"
    return "runtime"


def classify_execution_result(result: Mapping, generation_failed: bool = False) -> Tuple[str, str]:
    if generation_failed:
        return "generation_failed", "generation"
    if result.get("success") is True:
        if result.get("verified_success") is True:
            return "verified_passed", "none"
        return "process_passed", "none"

    error_type = str(result.get("error_type", ""))
    text = str(result.get("concise_error", "") or result.get("stderr", ""))
    category = classify_failure(error_type, text)
    outcomes = {
        "timeout": "timed_out",
        "dependency": "dependency_failed",
        "resource": "resource_failed",
        "infrastructure": "infra_failed",
        "syntax": "static_invalid",
    }
    return outcomes.get(category, "runtime_failed"), category


def is_knowledge_eligible_failure(record: Mapping) -> bool:
    if record.get("success") is not False:
        return False
    category = str(record.get("failure_category", "")).strip()
    if not category:
        category = classify_failure(
            str(record.get("error_type", "")),
            str(record.get("concise_error", "") or record.get("stderr", "")),
        )
    return category not in NON_KNOWLEDGE_CATEGORIES

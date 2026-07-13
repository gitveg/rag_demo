"""
processor.py — 执行闭环反馈离线处理器（薄编排层）。

从 execution_log.jsonl 读取执行结果，分三条回路收集候选：
  回路 A：成功代码 → 新知识单元
  回路 B：失败代码 → 错误记忆（原始信息，供人工分析）
  回路 C：失败代码 → API 约束

不再使用 LLM Judge（成本过高）。所有通过启发式预过滤的候选写入
pending_review.md 供人工在网页端审核；审核通过后由 --approve 执行入库。

用法：
    # 收集候选 + 生成 pending_review.md（不自动入库）
    python processor.py --log workspace/logs/execution_log.jsonl

    # 只跑某条回路
    python processor.py --log execution_log.jsonl --loop-b-only

    # 试运行（不写文件）
    python processor.py --log execution_log.jsonl --dry-run

    # 人工审核通过后入库
    python processor.py --approve pending_candidates_TIMESTAMP.json --ids "A:0,A:2,B:1,C:all"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAG_DEMO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, RAG_DEMO_ROOT)
sys.path.insert(0, SCRIPT_DIR)

from utils import (
    load_json,
    load_jsonl,
    save_json,
    append_jsonl,
    is_duplicate_unit,
    code_md5,
    load_api_kb,
    merge_constraints,
    merge_constraints_to_api_index,
)
from gates import LoopAGate, LoopBGate, LoopCGate
from event_schema import (
    record_event_id,
    sanitize_task_id,
    sha256_text,
    validate_execution_record,
)
from failure_classifier import is_knowledge_eligible_failure

# ==================== 配置 ====================

KB_DIR = os.path.join(RAG_DEMO_ROOT, "knowledge_base")
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
API_INDEX_FILE = os.path.join(KB_DIR, "genesis_api_index.json")
ERROR_MEMORY_FILE = os.path.join(KB_DIR, "genesis_error_memory.json")
UNIT_FILE = os.path.join(KB_DIR, "genesis_knowledge_units.json")
LOOP_NAMES = {"A": "loop_a", "B": "loop_b", "C": "loop_c"}
LOOP_DIRS = {kind: os.path.join(DATA_DIR, name) for kind, name in LOOP_NAMES.items()}
SUMMARY_FILES = {
    kind: os.path.join(DATA_DIR, f"{name}_summary.json")
    for kind, name in LOOP_NAMES.items()
}
CONSTRAINT_FILE = os.path.join(LOOP_DIRS["C"], "approved", "api_constraint.json")
PROGRESS_FILE = os.path.join(DATA_DIR, "state", "execution_feedback_progress.json")

UNIT_JACCARD_THRESHOLD = 0.8
ERROR_LOG_MAX_CHARS = 8000
MIN_APIS_FOR_UNIT = 3
MIN_CODE_LINES_FOR_UNIT = 20
MAX_EXAMPLES_PER_API = 6


# ==================== 回路 A：成功代码 → 知识单元候选 ====================

def collect_loop_a(records, known_apis, kb_class_ids, api_by_id,
                   existing_units):
    """
    收集回路 A 候选（不进行 LLM 审核）。
    复用 indexer_code.py GenesisImportVisitor + loop_a/metadata_gen.py。
    """
    from indexers.indexer_code import GenesisImportVisitor
    from indexers.indexer_knowledge_units import build_unit
    from loop_a.metadata_gen import generate_metadata
    import ast as _ast
    from api_id_normalize import resolve_api_to_known

    candidates = []

    for rec in records:
        # Process-level success is not enough to publish a reusable recipe.
        if rec.get("outcome") != "verified_passed":
            continue
        code_path = rec.get("code_path", "")
        query = rec.get("query", "")
        analysis = rec.get("execution_analysis", {})

        code = _read_code(code_path)
        if not code:
            continue

        # ---- 启发式预过滤 ----
        if code.count("\n") + 1 < MIN_CODE_LINES_FOR_UNIT:
            continue
        if not analysis.get("scene_build_started", False):
            continue

        # ---- AST 分析 ----
        try:
            tree = _ast.parse(code)
            visitor = GenesisImportVisitor(kb_class_ids)
            visitor.visit(tree)
            raw_apis = list(visitor.api_calls)
            all_apis = sorted(set(
                resolve_api_to_known(a, known_apis)
                for a in raw_apis
                if resolve_api_to_known(a, known_apis)
            ))
        except SyntaxError:
            continue

        if len(all_apis) < MIN_APIS_FOR_UNIT:
            continue

        if is_duplicate_unit(all_apis, existing_units + [c["unit"] for c in candidates], UNIT_JACCARD_THRESHOLD):
            print(f"    [SKIP]️ 重复单元: {code_path} (APIs={len(all_apis)})")
            continue

        # ---- 元数据生成 ----
        source_id = f"runtime_{record_event_id(rec)}_{code_md5(code)[:8]}"
        title, desc, tags = generate_metadata(code, query, source_id)

        # ---- 构建知识单元 ----
        key_apis = [a for a in all_apis if not a.startswith(("genesis.init", "genesis.Scene.build", "genesis.Scene.step"))]
        code_entry = {
            "id": f"{source_id}.py",
            "code": code,
            "metadata": {
                "title": title,
                "desc": desc,
                "tags": tags,
                "all_apis": all_apis,
                "key_apis": key_apis,
            },
        }
        unit = build_unit(code_entry, api_by_id)
        unit["source"] = "runtime_feedback"
        unit["query_context"] = query

        candidates.append({
            "candidate_id": _candidate_id("A", source_id),
            "type": "A",
            "source_id": source_id,
            "query": query,
            "all_apis": all_apis,
            "title": title,
            "desc": desc,
            "tags": tags,
            "code": code,
            "unit": unit,
        })
        print(f"    [CAND] 候选 A-{len(candidates)-1}: {source_id} | APIs={len(all_apis)} | {title}")

    return candidates


# ==================== 回路 B：失败代码 → 错误记忆候选 ====================

def collect_loop_b(records, existing_memory):
    """
    收集回路 B 候选（不调用 LLM Judge，仅收集原始错误信息供人工分析）。
    """
    from loop_b.judge import analyze_error

    candidates = []
    existing_ids = {item.get("id", "") for item in existing_memory}

    for rec in records:
        if not is_knowledge_eligible_failure(rec):
            continue
        code_path = rec.get("code_path", "")
        query = rec.get("query", "")
        stderr = rec.get("stderr", "")
        analysis = rec.get("execution_analysis", {})
        concise_error = rec.get("concise_error", "") or analysis.get("concise_error", "") or stderr

        # ---- 启发式预过滤 ----
        if not concise_error:
            continue
        if "ModuleNotFoundError" in concise_error:
            continue
        if "TimeoutError" in concise_error or "TimeoutExpired" in concise_error:
            continue
        if len(concise_error) > ERROR_LOG_MAX_CHARS:
            continue

        record_id = record_event_id(rec)
        if record_id in existing_ids:
            continue

        # ---- 收集原始错误信息（不含 LLM 分析）----
        raw = analyze_error(code_path, concise_error, file_id=record_id)
        if not raw:
            continue

        candidates.append({
            "candidate_id": _candidate_id("B", record_id),
            "type": "B",
            "record_id": record_id,
            "query": query,
            "code_path": code_path,
            "error_log": raw.get("error_log", concise_error),
            "raw": raw,
        })
        print(f"    [CAND] 候选 B-{len(candidates)-1}: {record_id} | {concise_error[:60]}")

    return candidates


# ==================== 回路 C：失败代码 → API 约束候选 ====================

def collect_loop_c(records, known_ids, class_ids, api_by_id,
                   existing_constraints):
    """
    收集回路 C 候选（启发式约束 + 人工审核）。
    """
    from loop_c.constraint_builder import (
        parse_error_events,
        map_events_to_api,
        _heuristic_constraints,
    )

    all_mapped = []
    for rec in records:
        if not is_knowledge_eligible_failure(rec):
            continue
        query = rec.get("query", "")
        record_id = record_event_id(rec)

        error_text = _record_error_text(rec)
        events = parse_error_events(error_text)
        mapped = map_events_to_api(events, known_ids, class_ids, record_id, query)
        all_mapped.extend(mapped)

    if not all_mapped:
        return []

    grouped = defaultdict(list)
    for m in all_mapped:
        grouped[m.api_id].append(m)

    candidates = []
    existing_map = {
        item.get("api_id", ""): set(item.get("constraints", []))
        for item in existing_constraints.get("apis", [])
        if isinstance(item, dict)
    }
    for api_id, events in sorted(grouped.items()):
        constraints = _heuristic_constraints(events)
        constraints = [c for c in constraints if c not in existing_map.get(api_id, set())]

        # 跳过无有效约束的 API（_heuristic_constraints 遇到不可泛化的错误现在返回空）
        if not constraints:
            continue

        error_examples = []
        seen = set()
        for e in events:
            msg = e.error_message.strip()
            if msg and msg not in seen:
                seen.add(msg)
                error_examples.append(msg)
            if len(error_examples) >= MAX_EXAMPLES_PER_API:
                break

        entry = {
            "api_id": api_id,
            "constraints": constraints,
            "error_examples": error_examples,
            "event_count": len(events),
            "sources": sorted({e.prompt_id for e in events}),
        }

        candidates.append({
            "candidate_id": _candidate_id("C", api_id, constraints),
            "type": "C",
            "api_id": api_id,
            "constraints": constraints,
            "error_examples": error_examples,
            "event_count": len(events),
            "entry": entry,
        })
        print(f"    [CAND] 候选 C-{len(candidates)-1}: {api_id} | {len(constraints)} 条约束 | events={len(events)}")

    return candidates


# ==================== 生成 pending_review 文档 ====================

def _run_label(log_file: str) -> str:
    """Return a compact, stable test label without losing the run timestamp."""
    source_stem = os.path.splitext(os.path.basename(log_file))[0]
    source_stem = re.sub(r"^execution_log_", "", source_stem)

    match = re.fullmatch(r"query100_part(\d+)", source_stem)
    if match:
        return f"q100-p{match.group(1)}"

    match = re.fullmatch(r"online(?:_authorized)?_\d{8}_(.+)", source_stem)
    if match:
        return f"online-{sanitize_task_id(match.group(1)).replace('_', '-') }"

    label = sanitize_task_id(source_stem, fallback="run").replace("_", "-")
    return label[:48].rstrip("-") or "run"


def _run_timestamp(timestamp: str) -> str:
    """Keep date and uniqueness while making a timestamp easier to scan."""
    return str(timestamp).replace("_", "-", 2)


def generate_pending_review(candidates, log_file, dry_run=False):
    """为单个回路生成一次运行的 review.md 和 candidates.json。"""
    if not candidates:
        return None, None
    loop_type = candidates[0]["type"]
    if loop_type not in LOOP_NAMES or any(c["type"] != loop_type for c in candidates):
        raise ValueError("generate_pending_review requires candidates from one loop")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_label = _run_label(log_file)
    run_timestamp = _run_timestamp(timestamp)
    review_id = f"{run_label}_{run_timestamp}"
    run_dir = os.path.join(LOOP_DIRS[loop_type], "runs", run_label, run_timestamp)

    os.makedirs(run_dir, exist_ok=True)

    counts = {"A": 0, "B": 0, "C": 0}
    for c in candidates:
        counts[c["type"]] = counts.get(c["type"], 0) + 1

    # ---- 生成 markdown ----
    md_lines = [
        f"# Pending Review — {timestamp}",
        "",
        f"- **Source log**: `{log_file}`",
        f"- **Total candidates**: {len(candidates)} (A: {counts.get('A', 0)}, B: {counts.get('B', 0)}, C: {counts.get('C', 0)})",
        f"- **Instructions**: 逐条审核，勾选 Approve 或 Reject，补充 Notes",
        "",
        "---",
        "",
    ]

    idx = {"A": 0, "B": 0, "C": 0}

    for c in candidates:
        t = c["type"]
        if t == "A":
            md_lines.append(f"## Loop A — 成功代码 → 知识单元")
            md_lines.append("")
            md_lines.append(LoopAGate.format_for_review(
                index=idx["A"],
                source_id=c["source_id"],
                query=c["query"],
                all_apis=c["all_apis"],
                title=c["title"],
                desc=c["desc"],
                tags=c["tags"],
                code=c["code"],
            ))
        elif t == "B":
            md_lines.append(f"## Loop B — 失败代码 → 错误记忆")
            md_lines.append("")
            md_lines.append(LoopBGate.format_for_review(
                index=idx["B"],
                record_id=c["record_id"],
                query=c["query"],
                error_log=c["error_log"],
                code_path=c.get("code_path", ""),
            ))
        elif t == "C":
            md_lines.append(f"## Loop C — 失败代码 → API 约束")
            md_lines.append("")
            md_lines.append(LoopCGate.format_for_review(
                index=idx["C"],
                api_id=c["api_id"],
                constraints=c["constraints"],
                error_examples=c["error_examples"],
                event_count=c["event_count"],
            ))
        idx[t] += 1
        md_lines.append("---")
        md_lines.append("")

    md_path = os.path.join(run_dir, "review.md")
    if not dry_run:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        print(f"\n pending_review 已写入: {md_path}")

    # ---- 保存结构化候选数据（供 --approve 使用）----
    serializable = []
    for c in candidates:
        sc = dict(c)
        # Keep the complete unit. approve mode must never ingest a review preview.
        if "unit" in sc:
            sc["unit"] = json.loads(json.dumps(sc["unit"], ensure_ascii=False))
        serializable.append(sc)

    json_path = os.path.join(run_dir, "candidates.json")
    if not dry_run:
        save_json(json_path, {
            "schema_version": 1,
            "loop": loop_type,
            "run_id": review_id,
            "generated_at": timestamp,
            "source_log": log_file,
            "counts": counts,
            "candidates": serializable,
        })
        print(f"[SAVE] pending_candidates 已写入: {json_path}")

    return md_path, json_path


def generate_pending_reviews(candidates, log_file, dry_run=False):
    """按回路拆分一次处理结果，并刷新每个回路的累计汇总。"""
    paths = {}
    for loop_type in LOOP_NAMES:
        loop_candidates = [c for c in candidates if c["type"] == loop_type]
        if not loop_candidates:
            continue
        paths[loop_type] = generate_pending_review(loop_candidates, log_file, dry_run=dry_run)
        if not dry_run:
            refresh_loop_summary(loop_type)
    return paths


def refresh_loop_summary(loop_type):
    """从某回路的所有运行归档重建跨测试的只读累计输出。"""
    if loop_type not in LOOP_NAMES:
        raise ValueError(f"unknown loop type: {loop_type}")

    runs_root = os.path.join(LOOP_DIRS[loop_type], "runs")
    run_files = []
    if os.path.isdir(runs_root):
        for root, _, files in os.walk(runs_root):
            if "candidates.json" in files:
                run_files.append(os.path.join(root, "candidates.json"))

    runs = []
    all_candidates = []
    for path in sorted(run_files):
        payload = load_json(path, default={})
        candidates = payload.get("candidates", [])
        if not isinstance(candidates, list):
            continue
        relative_path = os.path.relpath(path, LOOP_DIRS[loop_type]).replace(os.sep, "/")
        run = {
            "run_id": payload.get("run_id", os.path.basename(os.path.dirname(path))),
            "generated_at": payload.get("generated_at", ""),
            "source_log": payload.get("source_log", ""),
            "candidate_count": len(candidates),
            "candidates_file": relative_path,
        }
        runs.append(run)
        for candidate in candidates:
            all_candidates.append({
                "run_id": run["run_id"],
                "source_log": run["source_log"],
                "generated_at": run["generated_at"],
                "candidate": candidate,
            })

    save_json(SUMMARY_FILES[loop_type], {
        "schema_version": 1,
        "loop": loop_type,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "description": "跨测试累计候选；候选仍需人工审批，不能视为已入库知识。",
        "run_count": len(runs),
        "candidate_count": len(all_candidates),
        "runs": runs,
        "candidates": all_candidates,
    })
    return SUMMARY_FILES[loop_type]


def refresh_all_loop_summaries():
    return {loop_type: refresh_loop_summary(loop_type) for loop_type in LOOP_NAMES}


# ==================== 批准入库 ====================

def approve_and_ingest(candidates_file: str, approve_ids: str):
    """
    读取 pending_candidates JSON，按批准 ID 列表执行实际入库。

    approve_ids 格式: "A:0,A:2,B:1,C:all" 或 "0,1,2"（全局索引）
    """
    data = load_json(candidates_file)
    if not data:
        print("[FAIL] 无法读取候选文件")
        return

    candidates = data.get("candidates", [])
    if not candidates:
        print("[FAIL] 候选文件为空")
        return

    if not approve_ids or not approve_ids.strip():
        print("[FAIL] --ids 不能为空；审批默认 fail-closed")
        return

    # 解析批准 ID
    approved_set = _parse_approve_ids(approve_ids, candidates)

    _, known_api_ids, _ = load_api_kb(API_INDEX_FILE)
    valid_approved = set()
    for i in sorted(approved_set):
        errors = _validate_candidate(candidates[i], known_api_ids)
        if errors:
            cid = candidates[i].get("candidate_id", f"index:{i}")
            print(f"  [WARN]️ 拒绝无效候选 {cid}: {'; '.join(errors)}")
            continue
        valid_approved.add(i)
    approved_set = valid_approved

    # 按类型分组
    a_approved = []
    b_approved = []
    c_approved = []
    for i, c in enumerate(candidates):
        if i in approved_set:
            t = c["type"]
            if t == "A":
                a_approved.append(c)
            elif t == "B":
                b_approved.append(c)
            elif t == "C":
                c_approved.append(c)

    if not (a_approved or b_approved or c_approved):
        print("[FAIL] 没有匹配到任何候选")
        return

    # ---- 回路 A 入库 ----
    if a_approved:
        print(f"\n[SAVE] 回路 A 入库 {len(a_approved)} 个知识单元...")
        existing_units = load_json(UNIT_FILE, default=[])
        existing_unit_ids = {u.get("unit_id", "") for u in existing_units}
        for c in a_approved:
            unit = c["unit"]
            if unit.get("unit_id") in existing_unit_ids:
                print(f"  [WARN]️ 跳过重复 unit_id: {unit.get('unit_id')}")
                continue
            existing_units.append(unit)
            existing_unit_ids.add(unit.get("unit_id"))
            print(f"  [OK] {c['source_id']} | {c['title']}")
        save_json(UNIT_FILE, existing_units, backup=True)
        print(f"  已追加到 {UNIT_FILE}")

    # ---- 回路 B 入库 ----
    if b_approved:
        print(f"\n[SAVE] 回路 B 入库 {len(b_approved)} 条错误记忆...")
        existing_memory = load_json(ERROR_MEMORY_FILE, default=[])
        existing_patterns = {_normalize_text(item.get("bad_pattern", "")) for item in existing_memory}
        new_count = 0
        for c in b_approved:
            raw = c.get("raw", {})
            bad_pattern = raw.get("bad_pattern", "")
            normalized_pattern = _normalize_text(bad_pattern)
            if not normalized_pattern or normalized_pattern in existing_patterns:
                print(f"  [WARN]️ 跳过: {c['record_id']} (缺 bad_pattern 或重复)")
                continue
            existing_memory.append(raw)
            existing_patterns.add(normalized_pattern)
            new_count += 1
            print(f"  [OK] {c['record_id']} | {bad_pattern[:50]}")
        save_json(ERROR_MEMORY_FILE, existing_memory, backup=True)
        print(f"  已追加 {new_count} 条到 {ERROR_MEMORY_FILE}")

    # ---- 回路 C 入库 ----
    if c_approved:
        print(f"\n[SAVE] 回路 C 入库 {len(c_approved)} 个 API 约束...")
        existing_cons = load_json(CONSTRAINT_FILE, default={"apis": []})
        entries = [c["entry"] for c in c_approved]
        merge_constraints(existing_cons, entries, MAX_EXAMPLES_PER_API)
        existing_cons["generated_at"] = datetime.now().isoformat(timespec="seconds")
        existing_cons.setdefault("summary", {})["api_count"] = len(existing_cons.get("apis", []))
        save_json(CONSTRAINT_FILE, existing_cons, backup=True)
        for c in c_approved:
            print(f"  [OK] {c['api_id']} | {len(c['constraints'])} 条约束")
        print(f"  已更新 {CONSTRAINT_FILE}")

    print(f"\n[OK] 入库完成。")
    if c_approved:
        print(f"  -> 下一步: python processor.py --merge-constraints-to-api-index")
    print(f"  -> 最后: python rag_engine.py 重新灌库使变更生效")


def _parse_approve_ids(spec: str, candidates: list) -> set:
    """
    解析批准 ID 字符串。

    支持格式:
      - "A:0,A:2,B:1,C:all"  → 按类型+索引
      - "0,1,2,5"             → 全局索引
      - "all"                  → 全部
    """
    if not spec or not spec.strip():
        return set()
    if spec.strip().lower() == "all":
        return set(range(len(candidates)))

    approved = set()
    # 按类型索引
    type_indices = {"A": [], "B": [], "C": []}
    for i, c in enumerate(candidates):
        t = c["type"]
        if t in type_indices:
            type_indices[t].append(i)

    parts = [p.strip() for p in spec.split(",")]
    for p in parts:
        if ":" in p:
            t, idx_spec = p.split(":", 1)
            t = t.strip().upper()
            if t not in type_indices:
                continue
            if idx_spec.strip().lower() == "all":
                approved.update(type_indices[t])
            else:
                try:
                    local_idx = int(idx_spec.strip())
                    if 0 <= local_idx < len(type_indices[t]):
                        approved.add(type_indices[t][local_idx])
                except ValueError:
                    pass
        else:
            try:
                global_idx = int(p.strip())
                if 0 <= global_idx < len(candidates):
                    approved.add(global_idx)
            except ValueError:
                pass

    return approved


# ==================== 进度追踪 ====================

def _load_progress() -> dict:
    """加载进度文件，返回 {last_offset: int, processed_files: {...}}。"""
    return load_json(PROGRESS_FILE, default={"last_offset": 0, "processed_files": {}})


def _save_progress(progress: dict):
    """保存进度文件。"""
    progress["last_updated"] = datetime.now().isoformat(timespec="seconds")
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    save_json(PROGRESS_FILE, progress)


def _get_new_records(log_file: str, reprocess: bool = False) -> tuple:
    """
    读取执行日志，跳过已处理的行。

    Returns:
        (new_records, all_records, new_offset, has_existing_progress)
    """
    all_records = load_jsonl(log_file)
    if not all_records:
        return [], [], 0, False

    if reprocess:
        print(f"  [STAT] reprocess: 忽略历史进度，重新处理 {len(all_records)} 条 event")
        return all_records, all_records, len(all_records), False

    progress = _load_progress()
    processed_event_ids = set(progress.get("processed_event_ids", []))
    stored_offset = progress.get("processed_files", {}).get(os.path.basename(log_file), 0)

    if processed_event_ids:
        new_records = [r for r in all_records if record_event_id(r) not in processed_event_ids]
        skipped = len(all_records) - len(new_records)
        if skipped:
            print(f"  [STAT] 事件幂等: 已跳过 {skipped} 条已处理 event")
        has_progress = skipped > 0
    elif stored_offset > 0:
        print(f"  [STAT] 进度追踪: 已跳过 {stored_offset} 条（上次已处理）")
        new_records = all_records[stored_offset:]
        has_progress = True
    else:
        new_records = all_records
        has_progress = False

    new_offset = len(all_records)
    return new_records, all_records, new_offset, has_progress


def _update_progress(log_file: str, new_offset: int, stats: dict, processed_records=None):
    """更新进度文件。"""
    progress = _load_progress()
    progress["last_offset"] = new_offset
    progress.setdefault("processed_files", {})[os.path.basename(log_file)] = new_offset
    progress.setdefault("stats", {}).update(stats)
    processed = set(progress.get("processed_event_ids", []))
    for rec in processed_records or []:
        processed.add(record_event_id(rec))
    progress["processed_event_ids"] = sorted(processed)
    _save_progress(progress)


# ==================== 辅助函数 ====================

def _stable_id(rec):
    ts = rec.get("timestamp", "unknown").replace(":", "").replace("-", "").replace("T", "_")
    return f"{ts}_{rec.get('attempt', 1)}"


def _candidate_id(kind: str, *parts) -> str:
    payload = json.dumps([kind, *parts], ensure_ascii=False, sort_keys=True, default=str)
    return f"cand_{kind.lower()}_{sha256_text(payload)[:24]}"


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").lower().split())


def _read_text_file(path: str) -> str:
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _record_error_text(rec: dict) -> str:
    artifacts = rec.get("artifacts", {}) if isinstance(rec.get("artifacts"), dict) else {}
    artifact_text = _read_text_file(artifacts.get("traceback", ""))
    if artifact_text:
        return artifact_text
    concise = rec.get("concise_error", "")
    if concise:
        return concise
    return f"{rec.get('stdout', '')}\n{rec.get('stderr', '')}".strip()


def _validate_candidate(candidate: dict, known_api_ids: set) -> list[str]:
    errors = []
    kind = candidate.get("type")
    if kind == "A":
        unit = candidate.get("unit")
        required = {
            "unit_id", "title", "desc", "tags", "all_apis", "key_apis",
            "api_docs", "code", "embedding_text", "rerank_text",
        }
        if not isinstance(unit, dict):
            errors.append("unit must be an object")
        else:
            missing = sorted(required - set(unit))
            if missing:
                errors.append(f"unit missing fields: {', '.join(missing)}")
    elif kind == "B":
        raw = candidate.get("raw")
        if not isinstance(raw, dict):
            errors.append("raw must be an object")
        else:
            for field in ("bad_pattern", "correction", "explanation"):
                if not str(raw.get(field, "")).strip():
                    errors.append(f"raw.{field} is required")
            if not isinstance(raw.get("tags", []), list):
                errors.append("raw.tags must be a list")
    elif kind == "C":
        api_id = str(candidate.get("api_id", ""))
        constraints = candidate.get("constraints")
        if api_id not in known_api_ids:
            errors.append(f"unknown api_id: {api_id}")
        if not isinstance(constraints, list) or not constraints:
            errors.append("constraints must be a non-empty list")
        elif any(not isinstance(c, str) or not c.strip() for c in constraints):
            errors.append("constraints contain empty/non-string values")
        entry = candidate.get("entry")
        if not isinstance(entry, dict) or entry.get("api_id") != api_id:
            errors.append("entry.api_id does not match candidate.api_id")
        elif entry.get("constraints") != constraints:
            errors.append("entry.constraints does not match candidate.constraints")
    else:
        errors.append(f"unknown candidate type: {kind}")
    return errors


def _read_code(code_path):
    if not code_path or not os.path.exists(code_path):
        return ""
    try:
        with open(code_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _save_rejected(rejected, log_basename, loop_type="B"):
    if not rejected:
        return
    if loop_type not in LOOP_NAMES:
        raise ValueError(f"unknown loop type: {loop_type}")
    rejected_dir = os.path.join(LOOP_DIRS[loop_type], "rejected")
    os.makedirs(rejected_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(rejected_dir, f"rejected_{stamp}_{log_basename}.jsonl")
    for r in rejected:
        append_jsonl(path, r)
    print(f"   已保存 {len(rejected)} 条被拒记录 → {path}")


# ==================== 约束合并到 API 索引 ====================

def merge_constraints_to_index(constraint_file: str, api_index_file: str):
    """将 api_constraint.json 的约束合并到 genesis_api_index.json（审核通过后执行）。"""
    print(f"\n{'=' * 70}")
    print(f"合并约束 → API 索引")
    print(f"{'=' * 70}")
    print(f"约束文件: {constraint_file}")
    print(f"API 索引:  {api_index_file}")

    if not os.path.exists(constraint_file):
        print(f"[FAIL] 约束文件不存在: {constraint_file}")
        return

    constraints_data = load_json(constraint_file, default={"apis": []})
    constraint_apis = constraints_data.get("apis", [])
    if not constraint_apis:
        print("[FAIL] api_constraint.json 中没有约束数据")
        return

    print(f"[STAT] 约束覆盖 {len(constraint_apis)} 个 API")

    api_index = load_json(api_index_file, default=[])
    if not api_index:
        print(f"[FAIL] API 索引为空或不存在: {api_index_file}")
        return

    print(f" API 索引共 {len(api_index)} 个 API")

    # ---- 预览 ----
    print(f"\n{'─' * 50}")
    print(f"预览 — 即将合并的约束:")
    print(f"{'─' * 50}")
    for api in constraint_apis:
        api_id = api.get("api_id", "")
        cons = api.get("constraints", [])
        # 检查目标 API 是否存在于索引中
        found = any(e.get("api_id") == api_id for e in api_index)
        status = "✓" if found else "✗（API 不存在于索引中）"
        print(f"  {status} {api_id}: {len(cons)} 条约束")
        for c in cons:
            print(f"       - {c[:80]}{'...' if len(c) > 80 else ''}")

    # ---- 确认 ----
    missing = [a["api_id"] for a in constraint_apis
               if not any(e.get("api_id") == a["api_id"] for e in api_index)]
    if missing:
        print(f"\n[WARN]️  {len(missing)} 个 API 在索引中找不到，将被跳过: {missing}")

    print(f"\n将合并 {len(constraint_apis)} 个 API 的约束到 API 索引。")
    resp = input("确认合并？[y/N] ").strip().lower()
    if resp not in ("y", "yes"):
        print("已取消。")
        return

    # ---- 执行合并 ----
    merged = merge_constraints_to_api_index(api_index, constraint_file)
    save_json(api_index_file, merged, backup=True)

    # ---- 统计 ----
    merged_count = sum(1 for e in merged if e.get("constraints"))
    total_constraints = sum(len(e.get("constraints", [])) for e in merged)
    print(f"\n[OK] 合并完成")
    print(f"  索引中带约束的 API: {merged_count}")
    print(f"  总约束数: {total_constraints}")
    print(f"  已写回: {api_index_file}")
    print(f"\n  -> 下一步: python rag_engine.py 重新灌库使约束生效")


# ==================== 主流程 ====================

def run(log_file, loops="bc", dry_run=False, reprocess=False):
    print(f"\n{'=' * 70}")
    print(f"执行闭环反馈处理器（无 LLM Judge — 人工审核模式）")
    print(f"{'=' * 70}")
    print(
        f"日志: {log_file}  |  回路: {loops}  |  dry-run: {dry_run}"
        f"  |  reprocess: {reprocess}\n"
    )

    # ---- 进度追踪：仅处理新增记录 ----
    new_records, all_records, new_offset, has_progress = _get_new_records(
        log_file, reprocess=reprocess
    )
    if not new_records:
        if not dry_run and not reprocess and all_records:
            _update_progress(log_file, new_offset, {}, processed_records=all_records)
        print("[OK] 无新记录需要处理")
        return

    invalid_records = []
    valid_records = []
    for rec in new_records:
        errors = validate_execution_record(rec)
        if errors:
            invalid_records.append({"event_id": record_event_id(rec), "errors": errors})
        else:
            valid_records.append(rec)
    if invalid_records:
        print(f"  [WARN]️ 跳过 {len(invalid_records)} 条不满足事件契约的记录")
    new_records = valid_records

    successes = [r for r in new_records if r.get("success") is True]
    failures = [r for r in new_records if r.get("success") is False]
    print(f"[STAT] {len(new_records)} 条新记录: [OK] {len(successes)}  [FAIL] {len(failures)}")

    api_by_id, known_ids, class_ids = load_api_kb(API_INDEX_FILE)
    print(f" API 知识库: {len(known_ids)} 个 API\n")

    all_candidates = []

    # ---- 回路 A ----
    if loops in ("all", "a") and successes:
        print(f"{'─' * 50}")
        print(f"回路 A：成功代码 → 知识单元候选 ({len(successes)} 条)")
        print(f"{'─' * 50}")
        existing_units = load_json(UNIT_FILE, default=[])
        a_candidates = collect_loop_a(successes, known_ids, class_ids, api_by_id, existing_units)
        all_candidates.extend(a_candidates)

    # ---- 回路 B ----
    if loops in ("all", "b", "bc") and failures:
        print(f"\n{'─' * 50}")
        print(f"回路 B：失败代码 → 错误记忆候选 ({len(failures)} 条)")
        print(f"{'─' * 50}")
        existing_memory = load_json(ERROR_MEMORY_FILE, default=[])
        b_candidates = collect_loop_b(failures, existing_memory)
        all_candidates.extend(b_candidates)

    # ---- 回路 C ----
    if loops in ("all", "c", "bc") and failures:
        print(f"\n{'─' * 50}")
        print(f"回路 C：失败代码 → API 约束候选 ({len(failures)} 条)")
        print(f"{'─' * 50}")
        existing_cons = load_json(CONSTRAINT_FILE, default={"apis": []})
        c_candidates = collect_loop_c(failures, known_ids, class_ids, api_by_id, existing_cons)
        all_candidates.extend(c_candidates)

    # ---- 生成 pending_review 文档 ----
    if all_candidates:
        review_paths = generate_pending_reviews(all_candidates, log_file, dry_run=dry_run)
    else:
        review_paths = {}
        print("\n 无候选需要审核（全部被启发式预过滤或已存在）")

    # ---- 更新进度 ----
    stats = {
        "last_loop": loops,
        "candidates_A": sum(1 for c in all_candidates if c["type"] == "A"),
        "candidates_B": sum(1 for c in all_candidates if c["type"] == "B"),
        "candidates_C": sum(1 for c in all_candidates if c["type"] == "C"),
    }
    if not dry_run and not reprocess:
        _update_progress(log_file, new_offset, stats, processed_records=all_records)

    # ---- 汇总 ----
    print(f"\n{'=' * 70}")
    print(f"处理完成（待人工审核）")
    print(f"{'=' * 70}")
    print(f"  回路 A 候选: {sum(1 for c in all_candidates if c['type']=='A')}")
    print(f"  回路 B 候选: {sum(1 for c in all_candidates if c['type']=='B')}")
    print(f"  回路 C 候选: {sum(1 for c in all_candidates if c['type']=='C')}")
    if review_paths:
        for loop_type, (md_path, json_path) in review_paths.items():
            print(f"\n  Loop {loop_type} 待审文档: {md_path}")
            print(f"  [SAVE] Loop {loop_type} 候选数据: {json_path}")
            print(f"  -> 审核通过后: python processor.py --approve {json_path} --ids \"{loop_type}:all\"")
        print(f"\n  -> 下一步: 将 pending_review.md 发到网页端 Judge 审核")
    if dry_run:
        print(f"  [WARN]️ 试运行模式 — 未写入文件")


def main():
    parser = argparse.ArgumentParser(description="执行闭环反馈处理器（人工审核模式）")
    parser.add_argument("--log", help="execution_log.jsonl 路径（collect 模式必需）")
    parser.add_argument("--loops", default="bc", choices=["all", "a", "b", "c", "bc"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="忽略历史 progress 重新生成候选；不修改 progress，需配合显式 --loops",
    )
    parser.add_argument("--loop-b-only", action="store_true")
    parser.add_argument("--loop-a-only", action="store_true")
    parser.add_argument("--loop-c-only", action="store_true")
    # --approve 模式
    parser.add_argument("--approve", help="待批准的 pending_candidates JSON 文件路径")
    parser.add_argument("--ids", default="", help="批准哪些候选。默认空（fail-closed）；格式: \"A:0,A:2,B:1\"")
    # --merge-constraints-to-api-index 模式
    parser.add_argument(
        "--merge-constraints-to-api-index",
        action="store_true",
        help="将 api_constraint.json 的约束合并回 genesis_api_index.json（审核通过后执行，之后需重新灌库）",
    )
    parser.add_argument(
        "--constraint-file",
        default=None,
        help="约束文件路径（默认 feedback_loop/data/loop_c/approved/api_constraint.json）",
    )
    parser.add_argument(
        "--api-index-file",
        default=None,
        help="API 索引文件路径（默认 knowledge_base/genesis_api_index.json）",
    )
    args = parser.parse_args()

    # --merge-constraints-to-api-index 模式
    if args.merge_constraints_to_api_index:
        constraint_file = args.constraint_file or CONSTRAINT_FILE
        api_index_file = args.api_index_file or API_INDEX_FILE
        merge_constraints_to_index(constraint_file, api_index_file)
        return

    if args.approve:
        approve_and_ingest(args.approve, args.ids)
        return

    if not args.log:
        parser.error("collect 模式需要 --log；或使用 --approve <candidates.json>")

    loops = args.loops
    if args.loop_b_only: loops = "b"
    elif args.loop_a_only: loops = "a"
    elif args.loop_c_only: loops = "c"

    run(
        log_file=args.log,
        loops=loops,
        dry_run=args.dry_run,
        reprocess=args.reprocess,
    )


if __name__ == "__main__":
    main()

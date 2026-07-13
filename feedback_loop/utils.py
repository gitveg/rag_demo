"""
feedback_utils.py — 执行闭环反馈的共享工具函数。

提供：
  - JSON / JSONL 读写
  - AST API 提取（复用 indexer_code.py 的 GenesisImportVisitor）
  - 知识单元去重（Jaccard 相似度）
  - API ID 解析与映射
  - API 约束合并
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections import defaultdict
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

# 确保能 import rag_demo 根目录模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAG_DEMO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, RAG_DEMO_ROOT)

from api_id_normalize import normalize_api_id_for_kb, resolve_api_to_known


# ==================== JSON / JSONL ====================

def load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if not raw:
                return default
            return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return default


def save_json(path: str, data, backup: bool = False):
    """Atomically replace a JSON file and optionally retain its previous version."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{os.path.basename(path)}.", suffix=".tmp", dir=directory
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        if backup and os.path.exists(path):
            shutil.copy2(path, f"{path}.bak")
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def append_jsonl(path: str, record: dict):
    """追加一条 JSONL 记录（线程安全写入模式）。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_jsonl(path: str) -> List[dict]:
    """读取 JSONL 文件，跳过空行和解析失败的行。"""
    if not os.path.exists(path):
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"  ⚠️ JSONL 第 {line_no} 行解析失败，跳过")
    return records


# ==================== AST API 提取 ====================

def extract_apis_from_code(
    code: str,
    known_apis: Set[str],
    kb_class_ids: FrozenSet[str],
) -> Tuple[List[str], List[str]]:
    """
    从代码文本中提取 genesis.* API 引用，返回 (all_apis, key_apis)。
    复用 indexer_code.py 的 GenesisImportVisitor。
    """
    try:
        from indexers.indexer_code import GenesisImportVisitor
    except ImportError:
        # fallback：内联简化版
        return _extract_apis_simple(code, known_apis)

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return [], []

    visitor = GenesisImportVisitor(kb_class_ids)
    visitor.visit(tree)

    raw_apis = list(visitor.api_calls)
    filtered = []
    for api in raw_apis:
        canonical = resolve_api_to_known(api, known_apis)
        if canonical:
            filtered.append(canonical)

    all_apis = sorted(set(filtered))
    # key_apis 去掉 Scene.build, Scene.step, init 等基础 API
    _core_suffixes = (
        "genesis.init", "genesis.Scene.build", "genesis.Scene.step",
        "genesis.Scene.reset",
    )
    key_apis = [a for a in all_apis if not any(a.startswith(s) for s in _core_suffixes)]
    return all_apis, key_apis


def _extract_apis_simple(code: str, known_apis: Set[str]) -> Tuple[List[str], List[str]]:
    """简化版 API 提取（不依赖 GenesisImportVisitor，仅正则）。"""
    patterns = [
        r"gs\.([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*\(",
        r"genesis\.([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*\(",
    ]
    found = set()
    for pat in patterns:
        for m in re.finditer(pat, code):
            raw = m.group(0)
            if raw.startswith("gs."):
                raw = "genesis." + raw[3:]
            # 去掉尾部的 (
            raw = raw.rstrip("(").strip()
            canonical = resolve_api_to_known(raw, known_apis)
            if canonical:
                found.add(canonical)
    all_apis = sorted(found)
    return all_apis, all_apis


# ==================== 去重 ====================

def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def is_duplicate_unit(
    new_apis: List[str],
    existing_units: List[dict],
    threshold: float = 0.8,
) -> bool:
    """检查新单元是否与已有单元高度重复。"""
    new_set = set(new_apis)
    for unit in existing_units:
        existing_set = set(unit.get("all_apis", []))
        if not existing_set:
            continue
        sim = jaccard_similarity(new_set, existing_set)
        if sim >= threshold:
            return True
    return False


def code_md5(code: str) -> str:
    return hashlib.md5(code.encode("utf-8")).hexdigest()


# ==================== API ID 解析 ====================

def load_api_kb(api_index_file: str) -> Tuple[Dict[str, dict], Set[str], FrozenSet[str]]:
    """加载 API 知识库，返回 (by_id, known_ids, class_ids)。"""
    data = load_json(api_index_file, default=[])
    by_id = {}
    known_ids = set()
    class_ids = set()
    for r in data:
        if not isinstance(r, dict):
            continue
        api_id = r.get("api_id")
        if not api_id:
            continue
        by_id[api_id] = r
        known_ids.add(api_id)
        if r.get("type") == "class":
            class_ids.add(api_id)
    return by_id, known_ids, frozenset(class_ids)


# ==================== 约束合并 ====================

def merge_constraints(
    existing: dict,
    new_entries: List[dict],
    max_examples: int = 6,
) -> dict:
    """
    将新约束合并到已有的 api_constraint 结构中。

    existing: {"apis": [{"api_id": ..., "constraints": [...], ...}]}
    new_entries: [{"api_id": ..., "constraints": [...], "error_examples": [...], ...}]
    """
    existing_map = {api["api_id"]: api for api in existing.get("apis", [])}

    for entry in new_entries:
        aid = entry["api_id"]
        if aid in existing_map:
            target = existing_map[aid]
            # 合并约束（去重）
            old_cons = set(target.get("constraints", []))
            for c in entry.get("constraints", []):
                if c not in old_cons:
                    target.setdefault("constraints", []).append(c)
                    old_cons.add(c)
            # 合并 error_examples（去重，限制数量）
            old_examples = set(target.get("error_examples", []))
            for ex in entry.get("error_examples", []):
                if ex not in old_examples and len(target.get("error_examples", [])) < max_examples:
                    target.setdefault("error_examples", []).append(ex)
                    old_examples.add(ex)
            # 更新统计
            target["event_count"] = target.get("event_count", 0) + entry.get("event_count", 0)
            target.setdefault("sources", []).extend(entry.get("sources", []))
            target["sources"] = sorted(set(target["sources"]))
        else:
            existing_map[aid] = entry

    existing["apis"] = sorted(existing_map.values(), key=lambda x: x["api_id"])
    return existing


def merge_constraints_to_api_index(
    api_index: List[dict],
    constraint_file: str,
) -> List[dict]:
    """将 api_constraint.json 的约束合并到 API 索引中（用于重新灌库）。"""
    constraints_data = load_json(constraint_file, default={"apis": []})
    constraint_map = {api["api_id"]: api for api in constraints_data.get("apis", [])}

    for entry in api_index:
        aid = entry.get("api_id", "")
        if aid in constraint_map:
            existing_list = list(entry.get("constraints", []))
            existing = set(existing_list)
            new_cons = constraint_map[aid].get("constraints", [])
            entry["constraints"] = existing_list + [c for c in new_cons if c not in existing]

    return api_index


# ==================== 知识单元构建辅助 ====================

def build_unit_from_code(
    code: str,
    query: str,
    all_apis: List[str],
    key_apis: List[str],
    api_docs: List[dict],
    title: str,
    desc: str,
    tags: List[str],
    source_id: str,
) -> dict:
    """从执行成功的代码构建一个知识单元。"""
    code_preview = code[:1500]

    # embedding_text：HyDE 对齐的代码风格文本
    api_str = ", ".join(all_apis[:10])
    tags_str = ", ".join(tags[:5]) if tags else "general"
    embedding_text = (
        f"# {title}\n"
        f"# Domain: {tags_str}  |  APIs: {api_str}\n"
        f"# {desc}\n\n"
        f"{code_preview}"
    )

    # rerank_text：精简版供 cross-encoder
    key_str = ", ".join(key_apis[:5]) if key_apis else ""
    rerank_text = f"{title} | Domain: {tags_str} | {desc}"
    if key_str:
        rerank_text += f" | Key APIs: {key_str}"

    # API 文档摘要
    api_summaries = []
    for doc in api_docs:
        sig = doc.get("signature", "")
        summary = doc.get("summary", "")
        params = doc.get("parameters", "")
        api_summaries.append(f"- {doc.get('api_id', '')}: {sig}\n  {summary}\n  {params}")

    return {
        "unit_id": source_id,
        "title": title,
        "desc": desc,
        "tags": tags,
        "all_apis": all_apis,
        "key_apis": key_apis,
        "api_docs": [
            {
                "api_id": doc.get("api_id", ""),
                "signature": doc.get("signature", ""),
                "summary": doc.get("summary", ""),
                "params_preview": str(doc.get("parameters", ""))[:200],
            }
            for doc in api_docs
        ],
        "code": code,
        "embedding_text": embedding_text,
        "rerank_text": rerank_text,
        "source": "runtime_feedback",
        "query_context": query,
    }

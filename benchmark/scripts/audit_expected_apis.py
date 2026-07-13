#!/usr/bin/env python3
"""
检测 benchmark/query.json 中 expected_apis 的“API 幻觉”。

新增能力：
- 检测到“明确幻觉 API（源码不存在）”后，默认自动从 query.json 的 expected_apis 中删除。
- 记录删除操作并写入审计报告。
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set, Tuple


_PUBLIC_TO_CANONICAL_PREFIXES: Tuple[Tuple[str, str], ...] = (
    ("genesis.morphs.", "genesis.options.morphs."),
    ("genesis.sensors.", "genesis.options.sensors."),
    ("genesis.renderers.", "genesis.options.renderers."),
    ("genesis.surfaces.", "genesis.options.surfaces."),
    ("genesis.textures.", "genesis.options.textures."),
)


def normalize_api_id(api_id: str) -> str:
    api_id = (api_id or "").strip()
    for public, canonical in _PUBLIC_TO_CANONICAL_PREFIXES:
        if api_id.startswith(public):
            return canonical + api_id[len(public) :]
    return api_id


def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _parse_py_ast(path: str) -> ast.AST:
    with open(path, "r", encoding="utf-8") as f:
        return ast.parse(f.read(), filename=path)


def _iter_class_names(module_ast: ast.AST) -> Iterable[str]:
    for node in ast.walk(module_ast):
        if isinstance(node, ast.ClassDef):
            yield node.name


def _scene_methods(scene_py: str) -> Set[str]:
    out: Set[str] = set()
    tree = _parse_py_ast(scene_py)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Scene":
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    out.add(f"genesis.Scene.{item.name}")
            out.add("genesis.Scene")
            break
    return out


def _morph_apis(morphs_py: str) -> Set[str]:
    tree = _parse_py_ast(morphs_py)
    names = set(_iter_class_names(tree))
    out: Set[str] = set()
    for n in names:
        out.add(f"genesis.morphs.{n}")
        out.add(f"genesis.options.morphs.{n}")
    return out


def _options_apis(options_dir: str) -> Set[str]:
    out: Set[str] = set()
    init_py = os.path.join(options_dir, "__init__.py")
    if not os.path.exists(init_py):
        return out
    tree = _parse_py_ast(init_py)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                name = alias.asname or alias.name
                out.add(f"genesis.options.{name}")
                out.add(f"genesis.options.{node.module}.{alias.name}")
    return out


def _materials_apis(materials_dir: str) -> Set[str]:
    out: Set[str] = set()
    for root, _, files in os.walk(materials_dir):
        rel_root = os.path.relpath(root, materials_dir).replace("\\", "/")
        for fn in files:
            if not fn.endswith(".py") or fn == "__init__.py":
                continue
            py = os.path.join(root, fn)
            tree = _parse_py_ast(py)
            classes = list(_iter_class_names(tree))
            for cls in classes:
                if cls in {"Base", "Material"}:
                    continue
                if rel_root == ".":
                    out.add(f"genesis.materials.{cls}")
                else:
                    out.add(f"genesis.materials.{rel_root.replace('/', '.')}.{cls}")
    return out


def build_source_api_set(genesis_root: str) -> Set[str]:
    src: Set[str] = set()
    src |= _scene_methods(os.path.join(genesis_root, "engine", "scene.py"))
    src |= _morph_apis(os.path.join(genesis_root, "options", "morphs.py"))
    src |= _options_apis(os.path.join(genesis_root, "options"))
    src |= _materials_apis(os.path.join(genesis_root, "engine", "materials"))
    return src


@dataclass
class ApiCheck:
    api_id: str
    normalized: str
    in_source: bool
    in_kb: Optional[bool]
    tasks: List[str]


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    benchmark_dir = os.path.dirname(script_dir)
    repo_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))

    default_query = os.path.join(benchmark_dir, "query.json")
    default_out_dir = os.path.join(benchmark_dir, "results")
    default_root = os.path.join(repo_root, "Genesis", "genesis")
    default_kb = os.path.join(
        os.path.dirname(script_dir), "..", "knowledge_base", "genesis_api_index.json"
    )

    p = argparse.ArgumentParser(description="检测 query.json 的 expected_apis 幻觉 API，并可自动删除")
    p.add_argument("--query-file", default=default_query, help="benchmark query.json 路径")
    p.add_argument("--genesis-root", default=default_root, help="Genesis/genesis 源码根目录")
    p.add_argument("--kb-file", default=default_kb, help="可选：KB JSON 路径（不存在则跳过 KB 校验）")
    p.add_argument("--output-dir", default=default_out_dir, help="输出目录")
    p.add_argument("--no-apply-fix", action="store_true", help="仅检测，不修改 query.json")
    args = p.parse_args()

    apply_fix = not args.no_apply_fix
    tasks = _read_json(args.query_file)
    source_apis = build_source_api_set(args.genesis_root)

    kb_apis: Optional[Set[str]] = None
    if args.kb_file and os.path.exists(args.kb_file):
        kb = _read_json(args.kb_file)
        kb_apis = {x.get("api_id", "") for x in kb if isinstance(x, dict) and x.get("api_id")}

    api_to_tasks: Dict[str, Set[str]] = {}
    for t in tasks:
        tid = t.get("task_id", "unknown")
        for api in t.get("expected_apis", []) or []:
            api_to_tasks.setdefault(api, set()).add(tid)

    checks: List[ApiCheck] = []
    for api in sorted(api_to_tasks):
        normalized = normalize_api_id(api)
        in_source = (api in source_apis) or (normalized in source_apis)
        in_kb = None if kb_apis is None else ((api in kb_apis) or (normalized in kb_apis))
        checks.append(
            ApiCheck(
                api_id=api,
                normalized=normalized,
                in_source=in_source,
                in_kb=in_kb,
                tasks=sorted(api_to_tasks[api]),
            )
        )

    suspicious = [c for c in checks if not c.in_source]
    kb_missing = [c for c in checks if c.in_kb is False]
    suspicious_set = {c.api_id for c in suspicious}

    removal_ops: List[dict] = []
    removed_total = 0
    modified_task_count = 0
    backup_file = None
    query_updated = False

    if suspicious_set:
        for task in tasks:
            task_id = task.get("task_id", "unknown")
            expected = task.get("expected_apis", []) or []
            removed = [a for a in expected if a in suspicious_set]
            if not removed:
                continue
            new_expected = [a for a in expected if a not in suspicious_set]
            task["expected_apis"] = new_expected
            modified_task_count += 1
            removed_total += len(removed)
            removal_ops.append(
                {
                    "task_id": task_id,
                    "removed_apis": removed,
                    "before_count": len(expected),
                    "after_count": len(new_expected),
                }
            )

        if apply_fix and removal_ops:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{args.query_file}.bak.{ts}"
            shutil.copy2(args.query_file, backup_file)
            _write_json(args.query_file, tasks)
            query_updated = True

    os.makedirs(args.output_dir, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(args.output_dir, f"api_hallucination_audit_{run_id}.json")

    report = {
        "run_id": run_id,
        "query_file": args.query_file,
        "genesis_root": args.genesis_root,
        "kb_file": args.kb_file if kb_apis is not None else None,
        "total_unique_expected_apis": len(checks),
        "suspicious_count": len(suspicious),
        "kb_missing_count": len(kb_missing),
        "auto_fix": {
            "apply_fix": apply_fix,
            "query_updated": query_updated,
            "backup_file": backup_file,
            "modified_task_count": modified_task_count,
            "removed_api_total": removed_total,
            "operations": removal_ops,
        },
        "suspicious": [
            {
                "api_id": c.api_id,
                "normalized": c.normalized,
                "in_source": c.in_source,
                "in_kb": c.in_kb,
                "task_ids": c.tasks,
            }
            for c in suspicious
        ],
        "all_checks": [
            {
                "api_id": c.api_id,
                "normalized": c.normalized,
                "in_source": c.in_source,
                "in_kb": c.in_kb,
                "task_ids": c.tasks,
            }
            for c in checks
        ],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print("API Hallucination Audit")
    print(f"Query: {args.query_file}")
    print(f"Source APIs: {len(source_apis)}")
    print(f"Unique expected_apis: {len(checks)}")
    print(f"Suspicious: {len(suspicious)}")
    print(f"KB Missing (info): {len(kb_missing)}")
    if suspicious:
        print("\n可疑 API：")
        for c in suspicious:
            print(
                f"- {c.api_id} (normalized={c.normalized}, "
                f"in_source={c.in_source}, in_kb={c.in_kb}, tasks={','.join(c.tasks)})"
            )
    if removal_ops:
        print("\n自动修复：")
        print(f"- apply_fix: {apply_fix}")
        print(f"- modified_task_count: {modified_task_count}")
        print(f"- removed_api_total: {removed_total}")
        if backup_file:
            print(f"- backup_file: {backup_file}")
        for op in removal_ops:
            print(f"  * {op['task_id']}: removed={','.join(op['removed_apis'])}")
    print(f"\n报告已保存: {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()


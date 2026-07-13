#!/usr/bin/env python3
"""
分析 benchmark 结果中的未命中 API，并与本地 API 知识库对比。

能力：
1) 单次结果分析：区分 miss API 是「KB 不存在」还是「KB 存在但未召回」。
2) 批量结果分析：统计跨 run 的高频漏召回 API（仅统计 KB 存在但未召回）。
3) 输出 JSON + Markdown 两类报告，便于自动化与人工审查。
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


_PUBLIC_TO_CANONICAL_PREFIXES: Tuple[Tuple[str, str], ...] = (
    ("genesis.morphs.", "genesis.options.morphs."),
    ("genesis.sensors.", "genesis.options.sensors."),
    ("genesis.renderers.", "genesis.options.renderers."),
    ("genesis.surfaces.", "genesis.options.surfaces."),
    ("genesis.textures.", "genesis.options.textures."),
)


@dataclass
class MissRecord:
    task_id: str
    api_id: str
    normalized_api_id: str
    in_kb: bool
    source: str


def normalize_api_id(api_id: str) -> str:
    api_id = (api_id or "").strip()
    for public, canonical in _PUBLIC_TO_CANONICAL_PREFIXES:
        if api_id.startswith(public):
            return canonical + api_id[len(public) :]
    return api_id


def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def _write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def load_kb_apis(kb_file: str) -> tuple[Set[str], Set[str]]:
    kb = _read_json(kb_file)
    raw: Set[str] = set()
    norm: Set[str] = set()
    if isinstance(kb, list):
        for item in kb:
            if not isinstance(item, dict):
                continue
            api_id = (item.get("api_id") or "").strip()
            if not api_id:
                continue
            raw.add(api_id)
            norm.add(normalize_api_id(api_id))
    return raw, norm


def iter_result_jsons(path: str) -> Iterable[str]:
    if os.path.isfile(path):
        yield path
        return
    for root, _, files in os.walk(path):
        for fn in files:
            if fn.startswith("benchmark_") and fn.endswith(".json"):
                yield os.path.join(root, fn)


def _is_miss(info: Any) -> tuple[bool, str]:
    # 兼容新旧格式
    # - 新版: {"hit": bool, "source": "..."}
    # - 旧版: bool
    if isinstance(info, dict):
        source = str(info.get("source", "unknown"))
        hit = bool(info.get("hit", False))
        return (source == "miss") or (not hit and source in {"unknown", ""}), source
    if isinstance(info, bool):
        return not info, "unknown"
    return False, "unknown"


def analyze_single_result(result_json: str, kb_raw: Set[str], kb_norm: Set[str]) -> Dict[str, Any]:
    data = _read_json(result_json)
    tasks = data.get("tasks", []) if isinstance(data, dict) else []
    rag_params = data.get("rag_search_params", {}) if isinstance(data, dict) else {}

    miss_records: List[MissRecord] = []
    per_task_summary: List[Dict[str, Any]] = []

    for t in tasks:
        if not isinstance(t, dict):
            continue
        task_id = str(t.get("task_id", "unknown"))
        per_api = ((t.get("rag_hit") or {}).get("per_api") or {})
        if not isinstance(per_api, dict):
            continue

        missing_in_kb: List[str] = []
        exists_in_kb_but_missed: List[str] = []

        for api_id, info in per_api.items():
            is_miss, source = _is_miss(info)
            if not is_miss:
                continue
            api_s = str(api_id)
            api_norm = normalize_api_id(api_s)
            in_kb = (api_s in kb_raw) or (api_norm in kb_norm)
            miss_records.append(
                MissRecord(
                    task_id=task_id,
                    api_id=api_s,
                    normalized_api_id=api_norm,
                    in_kb=in_kb,
                    source=source,
                )
            )
            if in_kb:
                exists_in_kb_but_missed.append(api_s)
            else:
                missing_in_kb.append(api_s)

        if missing_in_kb or exists_in_kb_but_missed:
            per_task_summary.append(
                {
                    "task_id": task_id,
                    "missing_in_kb": sorted(set(missing_in_kb)),
                    "exists_in_kb_but_missed": sorted(set(exists_in_kb_but_missed)),
                    "missing_in_kb_count": len(set(missing_in_kb)),
                    "exists_in_kb_but_missed_count": len(set(exists_in_kb_but_missed)),
                }
            )

    missing_counter = Counter(r.api_id for r in miss_records if not r.in_kb)
    exists_counter = Counter(r.api_id for r in miss_records if r.in_kb)
    task_cov_counter: Dict[str, Set[str]] = defaultdict(set)
    for r in miss_records:
        task_cov_counter[r.api_id].add(r.task_id)

    total_miss = len(miss_records)
    missing_num = sum(1 for r in miss_records if not r.in_kb)
    exists_num = total_miss - missing_num

    priority_items = []
    for api_id, freq in exists_counter.items():
        task_cov = len(task_cov_counter.get(api_id, set()))
        priority_items.append(
            {
                "api_id": api_id,
                "miss_frequency": freq,
                "task_coverage": task_cov,
                "priority_score": freq * task_cov,
            }
        )
    priority_items.sort(key=lambda x: (-x["priority_score"], -x["miss_frequency"], x["api_id"]))

    return {
        "result_json": result_json,
        "run_id": data.get("run_id"),
        "timestamp": data.get("timestamp"),
        "rag_search_params": rag_params,
        "total_tasks": len(tasks) if isinstance(tasks, list) else 0,
        "total_miss_records": total_miss,
        "missing_in_kb_count": missing_num,
        "exists_in_kb_but_missed_count": exists_num,
        "missing_in_kb_ratio": round((missing_num / total_miss), 4) if total_miss else 0.0,
        "exists_in_kb_but_missed_ratio": round((exists_num / total_miss), 4) if total_miss else 0.0,
        "top_missing_in_kb": [{"api_id": k, "count": v} for k, v in missing_counter.most_common(30)],
        "top_exists_in_kb_but_missed": [{"api_id": k, "count": v} for k, v in exists_counter.most_common(30)],
        "priority_top_exists_in_kb_but_missed": priority_items[:50],
        "per_task": sorted(per_task_summary, key=lambda x: x["task_id"]),
    }


def build_batch_report(single_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    api_freq = Counter()
    api_task_cov: Dict[str, Set[str]] = defaultdict(set)
    api_run_cov: Dict[str, Set[str]] = defaultdict(set)

    for rep in single_reports:
        run_id = str(rep.get("run_id") or rep.get("result_json") or "unknown")
        for task in rep.get("per_task", []):
            task_id = task.get("task_id", "unknown")
            for api in task.get("exists_in_kb_but_missed", []):
                api_freq[api] += 1
                api_task_cov[api].add(task_id)
                api_run_cov[api].add(run_id)

    items = []
    for api, freq in api_freq.items():
        task_cov = len(api_task_cov.get(api, set()))
        run_cov = len(api_run_cov.get(api, set()))
        items.append(
            {
                "api_id": api,
                "miss_frequency": freq,
                "task_coverage": task_cov,
                "run_coverage": run_cov,
                "priority_score": freq * task_cov,
            }
        )
    items.sort(key=lambda x: (-x["priority_score"], -x["miss_frequency"], x["api_id"]))

    return {
        "run_count": len(single_reports),
        "high_freq_exists_in_kb_but_missed": items[:100],
    }


def render_markdown(single_reports: List[Dict[str, Any]], batch_report: Optional[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("# Benchmark 未命中 API 审查报告")
    lines.append("")
    lines.append(f"- 生成时间: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- 分析结果数: {len(single_reports)}")
    lines.append("")

    for rep in single_reports:
        lines.append(f"## Run: {rep.get('run_id') or 'unknown'}")
        lines.append(f"- 结果文件: `{rep.get('result_json')}`")
        lines.append(f"- 任务数: {rep.get('total_tasks', 0)}")
        lines.append(f"- miss 总数: {rep.get('total_miss_records', 0)}")
        lines.append(
            f"- KB 不存在: {rep.get('missing_in_kb_count', 0)} "
            f"({rep.get('missing_in_kb_ratio', 0.0) * 100:.1f}%)"
        )
        lines.append(
            f"- KB 存在但未召回: {rep.get('exists_in_kb_but_missed_count', 0)} "
            f"({rep.get('exists_in_kb_but_missed_ratio', 0.0) * 100:.1f}%)"
        )
        lines.append(f"- 检索参数: `{json.dumps(rep.get('rag_search_params', {}), ensure_ascii=False)}`")
        lines.append("")

        top_exists = rep.get("top_exists_in_kb_but_missed", [])
        if top_exists:
            lines.append("### Top KB 存在但未召回 API")
            for row in top_exists[:15]:
                lines.append(f"- `{row['api_id']}`: {row['count']}")
            lines.append("")

        top_missing = rep.get("top_missing_in_kb", [])
        if top_missing:
            lines.append("### Top KB 不存在 API")
            for row in top_missing[:15]:
                lines.append(f"- `{row['api_id']}`: {row['count']}")
            lines.append("")

    if batch_report:
        lines.append("## 跨 Run 高频漏召回（KB 存在但未召回）")
        lines.append(f"- Run 数: {batch_report.get('run_count', 0)}")
        rows = batch_report.get("high_freq_exists_in_kb_but_missed", [])
        for row in rows[:30]:
            lines.append(
                f"- `{row['api_id']}`: freq={row['miss_frequency']}, "
                f"task_cov={row['task_coverage']}, run_cov={row['run_coverage']}, "
                f"score={row['priority_score']}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    benchmark_dir = os.path.dirname(script_dir)
    repo_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))

    default_kb = os.path.join(
        os.path.dirname(script_dir), "..", "knowledge_base", "genesis_api_index.json"
    )
    p = argparse.ArgumentParser(description="分析 benchmark 结果中的 miss API 与 KB 覆盖关系")
    p.add_argument("--result-json", help="单个 benchmark_*.json 文件路径")
    p.add_argument("--results-dir", help="批量分析目录（递归扫描 benchmark_*.json）")
    p.add_argument("--kb-file", default=default_kb, help="API KB 文件路径")
    p.add_argument("--output-dir", help="报告输出目录（默认输出到被审查结果同目录）")
    args = p.parse_args()

    if not args.result_json and not args.results_dir:
        raise SystemExit("请至少提供 --result-json 或 --results-dir 之一。")

    if not os.path.exists(args.kb_file):
        raise SystemExit(f"KB 文件不存在: {args.kb_file}")

    result_paths: List[str] = []
    if args.result_json:
        result_paths.append(args.result_json)
    if args.results_dir:
        result_paths.extend(iter_result_jsons(args.results_dir))
    result_paths = sorted(set(result_paths))
    if not result_paths:
        raise SystemExit("未找到可分析的 benchmark_*.json。")

    kb_raw, kb_norm = load_kb_apis(args.kb_file)

    single_reports = [analyze_single_result(pth, kb_raw, kb_norm) for pth in result_paths]
    batch_report = build_batch_report(single_reports) if len(single_reports) > 1 else None

    if args.output_dir:
        output_dir = args.output_dir
    elif args.result_json:
        output_dir = os.path.dirname(os.path.abspath(args.result_json))
    else:
        output_dir = os.path.abspath(args.results_dir)

    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"benchmark_miss_kb_audit_{ts}"

    json_path = os.path.join(output_dir, f"{base}.json")
    md_path = os.path.join(output_dir, f"{base}.md")

    output = {
        "generated_at": datetime.now().isoformat(),
        "kb_file": args.kb_file,
        "kb_api_count": len(kb_raw),
        "result_count": len(single_reports),
        "single_reports": single_reports,
        "batch_report": batch_report,
    }
    _write_json(json_path, output)
    _write_text(md_path, render_markdown(single_reports, batch_report))

    print("=" * 60)
    print("Benchmark Miss API Audit")
    print(f"KB API count: {len(kb_raw)}")
    print(f"Analyzed results: {len(single_reports)}")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()

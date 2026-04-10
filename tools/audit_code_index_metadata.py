"""
审计 genesis_code_index.json 的元数据质量与覆盖度。

输出：
  report/code_index_metadata_audit_report.txt
  report/code_index_metadata_audit_report.json

运行（在 rag_demo/tools 下）：
  python audit_code_index_metadata.py
"""

from __future__ import annotations

import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple

# Windows 控制台 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAG_DEMO_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
KB_DIR = os.path.join(RAG_DEMO_DIR, "knowledge_base")
REPORT_DIR = os.path.join(RAG_DEMO_DIR, "report")

CODE_INDEX_FILE = os.path.join(KB_DIR, "genesis_code_index.json")
API_KB_FILE = os.path.join(KB_DIR, "genesis_api_index.json")

OUT_TXT = os.path.join(REPORT_DIR, "code_index_metadata_audit_report.txt")
OUT_JSON = os.path.join(REPORT_DIR, "code_index_metadata_audit_report.json")

# 与 indexer_code.py 保持一致（用于 tag 覆盖审计）
ALLOWED_TAGS = [
    "rigid_body", "soft_body", "fluid_mpm", "fluid_sph", "articulated_robot", "mixed_physics",
    "scene_creation", "motion_planning", "interaction", "rendering", "camera_control",
    "vis_export", "depth_sensing", "tactile_sensing",
]

if RAG_DEMO_DIR not in sys.path:
    sys.path.insert(0, RAG_DEMO_DIR)
from api_id_normalize import normalize_api_id_for_kb


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pct(n: int, d: int) -> float:
    return round(n / d, 6) if d else 0.0


def to_pct_str(v: float) -> str:
    return f"{v * 100:.2f}%"


def _len_stats(nums: List[int]) -> Dict[str, float]:
    if not nums:
        return {"min": 0, "p50": 0, "mean": 0, "p90": 0, "max": 0}
    s = sorted(nums)
    p50 = s[len(s) // 2]
    p90 = s[min(len(s) - 1, int(len(s) * 0.9))]
    return {
        "min": int(s[0]),
        "p50": int(p50),
        "mean": round(statistics.mean(s), 2),
        "p90": int(p90),
        "max": int(s[-1]),
    }


def analyze(code_index: List[dict], api_kb: List[dict]) -> Dict[str, Any]:
    total = len([e for e in code_index if isinstance(e, dict)])

    kb_api_set: Set[str] = set()
    for e in api_kb:
        aid = (e.get("api_id") or "").strip()
        if aid:
            kb_api_set.add(normalize_api_id_for_kb(aid))

    ids: List[str] = []
    duplicate_ids: Set[str] = set()

    tag_counter: Counter = Counter()
    unknown_tags: Counter = Counter()
    empty_tags_count = 0
    too_many_tags_count = 0

    empty_title_count = 0
    empty_desc_count = 0
    desc_len: List[int] = []
    code_len: List[int] = []

    empty_all_apis_count = 0
    empty_key_apis_count = 0
    key_not_in_all_count = 0
    all_not_in_kb_counter: Counter = Counter()
    key_not_in_kb_counter: Counter = Counter()

    all_api_counter: Counter = Counter()
    key_api_counter: Counter = Counter()
    all_per_entry: List[int] = []
    key_per_entry: List[int] = []

    tag_to_ids: Dict[str, List[str]] = defaultdict(list)

    for entry in code_index:
        if not isinstance(entry, dict):
            continue
        eid = str(entry.get("id") or "").strip()
        if eid in ids:
            duplicate_ids.add(eid)
        if eid:
            ids.append(eid)

        code = entry.get("code") or ""
        code_len.append(len(code))

        meta = entry.get("metadata") or {}
        title = str(meta.get("title") or "").strip()
        desc = str(meta.get("desc") or "").strip()
        tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []
        all_apis_raw = meta.get("all_apis") if isinstance(meta.get("all_apis"), list) else []
        key_apis_raw = meta.get("key_apis") if isinstance(meta.get("key_apis"), list) else []

        if not title:
            empty_title_count += 1
        if not desc or desc == "No description.":
            empty_desc_count += 1
        desc_len.append(len(desc))

        if not tags:
            empty_tags_count += 1
        if len(tags) > 3:
            too_many_tags_count += 1
        for t in tags:
            if not isinstance(t, str):
                continue
            tt = t.strip()
            if not tt:
                continue
            tag_counter[tt] += 1
            if eid:
                tag_to_ids[tt].append(eid)
            if tt not in ALLOWED_TAGS:
                unknown_tags[tt] += 1

        all_norm = sorted({
            normalize_api_id_for_kb(a.strip())
            for a in all_apis_raw
            if isinstance(a, str) and a.strip()
        })
        key_norm = sorted({
            normalize_api_id_for_kb(a.strip())
            for a in key_apis_raw
            if isinstance(a, str) and a.strip()
        })

        all_per_entry.append(len(all_norm))
        key_per_entry.append(len(key_norm))
        if not all_norm:
            empty_all_apis_count += 1
        if not key_norm:
            empty_key_apis_count += 1

        all_set = set(all_norm)
        key_set = set(key_norm)
        if not key_set.issubset(all_set):
            key_not_in_all_count += 1

        for a in all_norm:
            all_api_counter[a] += 1
            if a not in kb_api_set:
                all_not_in_kb_counter[a] += 1
        for a in key_norm:
            key_api_counter[a] += 1
            if a not in kb_api_set:
                key_not_in_kb_counter[a] += 1

    allowed_set = set(ALLOWED_TAGS)
    covered_allowed = sorted(allowed_set & set(tag_counter.keys()))
    uncovered_allowed = sorted(allowed_set - set(tag_counter.keys()))

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "paths": {
            "code_index": CODE_INDEX_FILE,
            "api_kb": API_KB_FILE,
            "output_txt": OUT_TXT,
            "output_json": OUT_JSON,
        },
        "counts": {
            "entries": total,
            "distinct_ids": len(set(ids)),
            "duplicate_id_count": len(duplicate_ids),
            "duplicate_ids": sorted(x for x in duplicate_ids if x),
        },
        "metadata_quality": {
            "empty_title": {"count": empty_title_count, "rate": pct(empty_title_count, total)},
            "empty_or_default_desc": {"count": empty_desc_count, "rate": pct(empty_desc_count, total)},
            "empty_tags": {"count": empty_tags_count, "rate": pct(empty_tags_count, total)},
            "tag_count_gt_3": {"count": too_many_tags_count, "rate": pct(too_many_tags_count, total)},
            "description_length": _len_stats(desc_len),
            "code_length": _len_stats(code_len),
        },
        "tag_coverage": {
            "allowed_tags_total": len(ALLOWED_TAGS),
            "covered_allowed_tags": len(covered_allowed),
            "covered_allowed_rate": pct(len(covered_allowed), len(ALLOWED_TAGS)),
            "covered_allowed_tags_list": covered_allowed,
            "uncovered_allowed_tags_list": uncovered_allowed,
            "unknown_tags": dict(unknown_tags.most_common()),
            "tag_distribution": dict(tag_counter.most_common()),
            "tag_presence_by_entry_top20": {
                k: len(set(v))
                for k, v in sorted(tag_to_ids.items(), key=lambda x: -len(set(x[1])))[:20]
            },
        },
        "api_field_quality": {
            "empty_all_apis": {"count": empty_all_apis_count, "rate": pct(empty_all_apis_count, total)},
            "empty_key_apis": {"count": empty_key_apis_count, "rate": pct(empty_key_apis_count, total)},
            "key_not_subset_of_all": {"count": key_not_in_all_count, "rate": pct(key_not_in_all_count, total)},
            "all_apis_per_entry": _len_stats(all_per_entry),
            "key_apis_per_entry": _len_stats(key_per_entry),
            "distinct_all_apis": len(all_api_counter),
            "distinct_key_apis": len(key_api_counter),
            "top_all_apis": dict(all_api_counter.most_common(30)),
            "top_key_apis": dict(key_api_counter.most_common(30)),
        },
        "kb_alignment": {
            "api_kb_distinct": len(kb_api_set),
            "all_apis_not_in_kb_distinct": len(all_not_in_kb_counter),
            "key_apis_not_in_kb_distinct": len(key_not_in_kb_counter),
            "all_apis_not_in_kb_top50": dict(all_not_in_kb_counter.most_common(50)),
            "key_apis_not_in_kb_top50": dict(key_not_in_kb_counter.most_common(50)),
        },
    }
    return report


def write_text_report(report: Dict[str, Any], path: str) -> None:
    c = report["counts"]
    mq = report["metadata_quality"]
    tg = report["tag_coverage"]
    aq = report["api_field_quality"]
    kb = report["kb_alignment"]

    lines: List[str] = []
    lines += [
        "genesis_code_index 元数据审计报告",
        "=" * 80,
        f"生成时间: {report['generated_at']}",
        f"代码范例库: {report['paths']['code_index']}",
        f"API 知识库 : {report['paths']['api_kb']}",
        "",
        "一、总体规模",
        "-" * 80,
        f"  范例条目数                 : {c['entries']:,}",
        f"  唯一 id 数                 : {c['distinct_ids']:,}",
        f"  重复 id 数                 : {c['duplicate_id_count']:,}",
    ]
    if c["duplicate_ids"]:
        lines.append("  重复 id 列表:")
        lines.extend([f"    - {x}" for x in c["duplicate_ids"][:100]])

    lines += [
        "",
        "二、metadata 质量",
        "-" * 80,
        f"  空 title                    : {mq['empty_title']['count']:,} ({to_pct_str(mq['empty_title']['rate'])})",
        f"  空/默认 desc                : {mq['empty_or_default_desc']['count']:,} ({to_pct_str(mq['empty_or_default_desc']['rate'])})",
        f"  空 tags                     : {mq['empty_tags']['count']:,} ({to_pct_str(mq['empty_tags']['rate'])})",
        f"  tags 数量 > 3               : {mq['tag_count_gt_3']['count']:,} ({to_pct_str(mq['tag_count_gt_3']['rate'])})",
        f"  desc 长度统计               : {mq['description_length']}",
        f"  code 长度统计               : {mq['code_length']}",
        "",
        "三、场景/标签覆盖（重点）",
        "-" * 80,
        f"  允许标签总数                : {tg['allowed_tags_total']}",
        f"  覆盖到的允许标签            : {tg['covered_allowed_tags']} ({to_pct_str(tg['covered_allowed_rate'])})",
        f"  未覆盖允许标签数            : {len(tg['uncovered_allowed_tags_list'])}",
        f"  未覆盖允许标签              : {tg['uncovered_allowed_tags_list']}",
        f"  未知标签（不在允许池）种数   : {len(tg['unknown_tags'])}",
    ]
    if tg["unknown_tags"]:
        lines.append("  未知标签 Top:")
        for k, v in list(tg["unknown_tags"].items())[:30]:
            lines.append(f"    - {k}: {v}")

    lines += [
        "",
        "  Tag 分布 Top 20:",
    ]
    for k, v in list(tg["tag_distribution"].items())[:20]:
        lines.append(f"    - {k:<22} {v:>5}")

    lines += [
        "",
        "四、API 字段质量",
        "-" * 80,
        f"  空 all_apis                 : {aq['empty_all_apis']['count']:,} ({to_pct_str(aq['empty_all_apis']['rate'])})",
        f"  空 key_apis                 : {aq['empty_key_apis']['count']:,} ({to_pct_str(aq['empty_key_apis']['rate'])})",
        f"  key_apis 非 all_apis 子集    : {aq['key_not_subset_of_all']['count']:,} ({to_pct_str(aq['key_not_subset_of_all']['rate'])})",
        f"  all_apis 每条统计            : {aq['all_apis_per_entry']}",
        f"  key_apis 每条统计            : {aq['key_apis_per_entry']}",
        f"  distinct all_apis           : {aq['distinct_all_apis']:,}",
        f"  distinct key_apis           : {aq['distinct_key_apis']:,}",
        "",
        "  all_apis Top 20:",
    ]
    for k, v in list(aq["top_all_apis"].items())[:20]:
        lines.append(f"    - {k:<40} {v:>5}")

    lines += [
        "",
        "  key_apis Top 20:",
    ]
    for k, v in list(aq["top_key_apis"].items())[:20]:
        lines.append(f"    - {k:<40} {v:>5}")

    lines += [
        "",
        "五、与 API 知识库对齐",
        "-" * 80,
        f"  API KB distinct             : {kb['api_kb_distinct']:,}",
        f"  all_apis 不在 KB 的种数      : {kb['all_apis_not_in_kb_distinct']:,}",
        f"  key_apis 不在 KB 的种数      : {kb['key_apis_not_in_kb_distinct']:,}",
        "",
        "  key_apis 不在 KB Top 30:",
    ]
    if not kb["key_apis_not_in_kb_top50"]:
        lines.append("    - （无）")
    else:
        for k, v in list(kb["key_apis_not_in_kb_top50"].items())[:30]:
            lines.append(f"    - {k}: {v}")

    lines += [
        "",
        "=" * 80,
        f"详细 JSON: {OUT_JSON}",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    if not os.path.isfile(CODE_INDEX_FILE):
        print(f"未找到: {CODE_INDEX_FILE}")
        sys.exit(1)
    if not os.path.isfile(API_KB_FILE):
        print(f"未找到: {API_KB_FILE}")
        sys.exit(1)

    os.makedirs(REPORT_DIR, exist_ok=True)

    code_index = load_json(CODE_INDEX_FILE)
    api_kb = load_json(API_KB_FILE)
    if not isinstance(code_index, list) or not isinstance(api_kb, list):
        print("输入 JSON 根必须为数组。")
        sys.exit(1)

    report = analyze(code_index, api_kb)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    write_text_report(report, OUT_TXT)

    print(f"entries={report['counts']['entries']:,}")
    print(
        f"tag_covered={report['tag_coverage']['covered_allowed_tags']}/"
        f"{report['tag_coverage']['allowed_tags_total']}"
    )
    print(f"empty_key_apis={report['api_field_quality']['empty_key_apis']['count']:,}")
    print(f"TXT : {OUT_TXT}")
    print(f"JSON: {OUT_JSON}")


if __name__ == "__main__":
    main()


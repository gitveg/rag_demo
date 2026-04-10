"""
代码范例库 vs API 知识库 —— 覆盖检测报告
========================================
对比 genesis_code_index.json 中全部 metadata.key_apis 与
genesis_api_index.json 中的 api_id：
  - API 库中有多少 api_id 至少出现在某一范例的 key_apis 中（精确匹配，经归一化）
  - 缺失列表、范例库中多出的 id、按文件统计

运行（在 rag_demo/tools 下）:
  python audit_code_index_api_coverage.py

输出:
  knowledge_base/code_index_api_coverage_report.txt
  knowledge_base/code_index_api_coverage_report.json
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Set

# UTF-8 控制台
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_RAG_DEMO = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
_KB_DIR = os.path.join(_RAG_DEMO, "knowledge_base")

KB_API = os.path.join(_KB_DIR, "genesis_api_index.json")
KB_CODE = os.path.join(_KB_DIR, "genesis_code_index.json")
OUT_TXT = os.path.join(_KB_DIR, "code_index_api_coverage_report.txt")
OUT_JSON = os.path.join(_KB_DIR, "code_index_api_coverage_report.json")

# 写入报告与 JSON，避免把「key_apis 缺失」误读成「范例源码未使用该 API」
METHODOLOGY_NOTE = (
    "【重要说明】本报告对比的是「每条范例 metadata.key_apis」与「API 库 api_id」两个字符串集合。\n"
    "key_apis 由 indexer_code.py 的 AST 访问器生成：只有调用链能从 import 映射到 genesis.* 时才会\n"
    "记录。例如 gs.Scene(...) 会得到 genesis.Scene；但 scene.add_entity(...)、scene.build() 里左侧\n"
    "是局部变量 scene，AST 无法解析出类型，因此不会写入 genesis.Scene.add_entity / genesis.Scene.build。\n"
    "同理，实体上的 .set_velocity、.get_state 等实例方法也大量不会被记入 key_apis。\n"
    "因此下列「未覆盖」只表示：没有任何范例的 key_apis 字段出现过该 api_id；不代表 examples 源码里\n"
    "没有调用这些 API。若要做「源码级」覆盖，需要对 AST 做简单的 defs/赋值追踪或补充正则扫描。"
)

if _RAG_DEMO not in sys.path:
    sys.path.insert(0, _RAG_DEMO)
from api_id_normalize import normalize_api_id_for_kb


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def collect_kb_api_ids(api_kb: List[dict]) -> Set[str]:
    out: Set[str] = set()
    for e in api_kb:
        aid = (e.get("api_id") or "").strip()
        if aid:
            out.add(normalize_api_id_for_kb(aid))
    return out


def collect_code_index_apis(code_index: List[dict]):
    """返回 (归一化后的 api 集合, api -> 出现过的范例 id 列表)。"""
    apis: Set[str] = set()
    api_to_files: Dict[str, List[str]] = defaultdict(list)

    for entry in code_index:
        if not isinstance(entry, dict):
            continue
        file_id = entry.get("id") or entry.get("file") or "<unknown>"
        meta = entry.get("metadata") or {}
        keys = meta.get("key_apis") or []
        if not isinstance(keys, list):
            continue
        for raw in keys:
            s = (raw or "").strip()
            if not s:
                continue
            norm = normalize_api_id_for_kb(s)
            apis.add(norm)
            if file_id not in api_to_files[norm]:
                api_to_files[norm].append(file_id)

    return apis, dict(api_to_files)


def build_report(api_kb: List[dict], code_index: List[dict]) -> Dict[str, Any]:
    kb_set = collect_kb_api_ids(api_kb)
    code_set, api_to_files = collect_code_index_apis(code_index)

    missing = sorted(kb_set - code_set)
    orphans = sorted(code_set - kb_set)
    covered = kb_set & code_set

    # 每个缺失 API 在 KB 中的 type（若有）
    kb_type: Dict[str, str] = {}
    for e in api_kb:
        aid = (e.get("api_id") or "").strip()
        if not aid:
            continue
        kb_type[normalize_api_id_for_kb(aid)] = (e.get("type") or "").strip() or "?"

    missing_with_type = [{"api_id": m, "kb_type": kb_type.get(m, "?")} for m in missing]

    # 范例条数、key_apis 总出现次数（含跨文件重复）
    total_key_mentions = 0
    for entry in code_index:
        if not isinstance(entry, dict):
            continue
        meta = entry.get("metadata") or {}
        keys = meta.get("key_apis") or []
        if isinstance(keys, list):
            total_key_mentions += sum(1 for x in keys if (x or "").strip())

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "methodology_note": METHODOLOGY_NOTE,
        "paths": {"api_kb": KB_API, "code_index": KB_CODE},
        "counts": {
            "api_kb_distinct": len(kb_set),
            "code_index_entries": len([e for e in code_index if isinstance(e, dict)]),
            "code_index_distinct_key_apis": len(code_set),
            "key_apis_total_mentions": total_key_mentions,
            "covered_apis": len(covered),
            "missing_apis": len(missing),
            "orphan_key_apis": len(orphans),
        },
        "coverage_rate": round(len(covered) / len(kb_set), 6) if kb_set else 0.0,
        "missing_api_ids": missing,
        "missing_detail": missing_with_type,
        "orphan_key_apis": orphans,
        # 仅保留「被引用次数最多」的若干 API，完整映射见需可自行扫 api_to_files
        "sample_covered_files": {
            api: files[:5]
            for api, files in sorted(
                ((a, api_to_files[a]) for a in covered),
                key=lambda x: -len(x[1]),
            )[:20]
        },
    }


def write_text_report(data: Dict[str, Any], path: str) -> None:
    c = data["counts"]
    lines = [
        "代码范例库 key_apis 对 API 知识库覆盖检测报告",
        "=" * 72,
        f"生成时间: {data['generated_at']}",
        f"API 库文件: {data['paths']['api_kb']}",
        f"范例库文件: {data['paths']['code_index']}",
        "",
        "〇、重要说明（请先读，避免误读覆盖率）",
        "-" * 72,
    ]
    for para in data.get("methodology_note", METHODOLOGY_NOTE).split("\n"):
        if para.strip():
            lines.append(f"  {para}")
    lines.extend(
        [
        "",
        "一、汇总",
        "-" * 72,
        f"  API 知识库 distinct api_id 数     : {c['api_kb_distinct']:,}",
        f"  代码范例库条目数（脚本个数）       : {c['code_index_entries']:,}",
        f"  范例库 distinct key_apis 数         : {c['code_index_distinct_key_apis']:,}",
        f"  key_apis 字段总条数（含重复）      : {c['key_apis_total_mentions']:,}",
        f"  已被至少一个范例 key_apis 覆盖的 API: {c['covered_apis']:,}",
        f"  知识库有、但范例库未覆盖的 API      : {c['missing_apis']:,}",
        f"  范例库出现、但知识库无此 api_id     : {c['orphan_key_apis']:,}",
        f"  覆盖率（覆盖数 / API 库 distinct）  : {data['coverage_rate'] * 100:.2f}%",
        "",
        "二、知识库中有、但任一范例的 key_apis 均未出现的 api_id（完整列表）",
        "-" * 72,
        ],
    )
    if not data["missing_api_ids"]:
        lines.append("  （无）全部 API 均在某范例的 key_apis 中出现。")
    else:
        lines.append(
            "  （见上文〇节：大量 Scene 实例方法会出现在源码中但不在 key_apis 里。）"
        )
        for m in data["missing_api_ids"]:
            t = next((x["kb_type"] for x in data["missing_detail"] if x["api_id"] == m), "?")
            lines.append(f"  [{t}] {m}")

    lines.extend(
        [
            "",
            "三、范例库 key_apis 中出现但 API 知识库不存在的 id（数据一致性）",
            "-" * 72,
        ]
    )
    if not data["orphan_key_apis"]:
        lines.append("  （无）")
    else:
        for o in data["orphan_key_apis"]:
            lines.append(f"  {o}")

    lines.extend(
        [
            "",
            "四、引用范例最多的 API 示例（每项最多列 5 个文件名）",
            "-" * 72,
        ]
    )
    for api, files in data["sample_covered_files"].items():
        lines.append(f"  {api}")
        for f in files:
            lines.append(f"      - {f}")

    lines.append("")
    lines.append("=" * 72)
    lines.append("详细机器可读数据见: code_index_api_coverage_report.json")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    if not os.path.isfile(KB_API):
        print(f"未找到 API 知识库: {KB_API}")
        sys.exit(1)
    if not os.path.isfile(KB_CODE):
        print(f"未找到代码范例库: {KB_CODE}")
        sys.exit(1)

    api_kb = load_json(KB_API)
    code_index = load_json(KB_CODE)
    if not isinstance(api_kb, list) or not isinstance(code_index, list):
        print("JSON 根类型应为数组。")
        sys.exit(1)

    report = build_report(api_kb, code_index)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    write_text_report(report, OUT_TXT)

    print(report["paths"]["api_kb"])
    print(report["paths"]["code_index"])
    print()
    print(
        f"API 库 {report['counts']['api_kb_distinct']} 条 | "
        f"已覆盖 {report['counts']['covered_apis']} | "
        f"缺失 {report['counts']['missing_apis']} | "
        f"覆盖率 {report['coverage_rate'] * 100:.2f}%"
    )
    print(f"文本报告: {OUT_TXT}")
    print(f"JSON 报告: {OUT_JSON}")


if __name__ == "__main__":
    main()

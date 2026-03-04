"""
知识库健康度评估脚本
====================
评估三个知识库的质量指标，输出控制台报告 + JSON 数据文件。

知识库：
  1. genesis_knowledge_base_final.json  —— API 知识库
  2. genesis_code_index.json            —— 代码范例库
  3. genesis_code_snippets.json         —— 代码片段库

运行：
  python kb_health_check.py
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime

# 强制 stdout 使用 UTF-8，避免 Windows GBK 终端的编码错误
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─────────────────────────── 配置 ───────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

KB_API      = os.path.join(SCRIPT_DIR, "genesis_knowledge_base_final.json")
KB_CODE     = os.path.join(SCRIPT_DIR, "genesis_code_index.json")
KB_SNIPPETS = os.path.join(SCRIPT_DIR, "genesis_code_snippets.json")
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "kb_health_report.json")

# 控制台打印时，Tag / Key-API 最多显示的条数
TOP_N = 15

NO_SUMMARY_SENTINEL = "No summary available."


# ─────────────────────────── 工具函数 ───────────────────────────
def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fmt_pct(num: int, total: int) -> str:
    pct = num / total * 100 if total else 0
    return f"{num:>6,} / {total:,}  ({pct:.1f}%)"


def print_section(title: str):
    width = 60
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def print_counter(counter: Counter, label: str, top_n: int = TOP_N):
    """打印 Counter，超出 top_n 的部分折叠为'其他'。"""
    total_items = len(counter)
    top = counter.most_common(top_n)
    rest_count = total_items - top_n

    print(f"\n  [{label}]  共 {total_items} 种")
    print(f"  {'名称':<45} {'出现次数':>8}")
    print(f"  {'-'*45} {'-'*8}")
    for name, cnt in top:
        # 截断过长的名称
        display = name if len(name) <= 44 else name[:41] + "..."
        print(f"  {display:<45} {cnt:>8,}")
    if rest_count > 0:
        print(f"  {'... 其余 ' + str(rest_count) + ' 种（详见 JSON 报告）':<45}")


# ─────────────────────────── 1. API 知识库 ───────────────────────────
def analyze_api_kb(data: list) -> dict:
    total = len(data)

    has_summary     = sum(1 for e in data if e.get("summary", NO_SUMMARY_SENTINEL) != NO_SUMMARY_SENTINEL
                          and e.get("summary", "").strip())
    has_constraints = sum(1 for e in data if e.get("constraints"))
    is_core         = sum(1 for e in data if "core" in e.get("domain_tags", []))

    # 按 type 分布
    type_counter = Counter(e.get("type", "unknown") for e in data)

    # 按模块（api_id 第一段）分布，取前缀
    module_counter = Counter()
    for e in data:
        api_id = e.get("api_id", "")
        parts = api_id.split(".")
        module = ".".join(parts[:2]) if len(parts) >= 2 else parts[0]
        module_counter[module] += 1

    return {
        "total": total,
        "summary_coverage": {"count": has_summary, "rate": round(has_summary / total, 4) if total else 0},
        "constraints_coverage": {"count": has_constraints, "rate": round(has_constraints / total, 4) if total else 0},
        "core_api_count": is_core,
        "type_distribution": dict(type_counter.most_common()),
        "module_distribution": dict(module_counter.most_common(50)),
    }


def print_api_kb(result: dict):
    print_section("1. API 知识库 (genesis_knowledge_base_final.json)")
    total = result["total"]
    print(f"\n  总条目数         : {total:,}")
    print(f"  Summary 覆盖率   : {fmt_pct(result['summary_coverage']['count'], total)}")
    print(f"  Constraints 覆盖 : {fmt_pct(result['constraints_coverage']['count'], total)}")
    print(f"  Core API 数量    : {result['core_api_count']:,}")

    print(f"\n  [类型分布]")
    for t, cnt in result["type_distribution"].items():
        print(f"    {t:<20} {cnt:>6,}")

    print(f"\n  [Top-{TOP_N} 模块（按 api_id 前两段分组）]")
    print(f"  {'模块':<45} {'条目数':>8}")
    print(f"  {'-'*45} {'-'*8}")
    for mod, cnt in list(result["module_distribution"].items())[:TOP_N]:
        display = mod if len(mod) <= 44 else mod[:41] + "..."
        print(f"  {display:<45} {cnt:>8,}")


# ─────────────────────────── 2. 代码范例库 ───────────────────────────
def analyze_code_index(data: list) -> dict:
    total = len(data)
    tag_counter = Counter()
    api_counter = Counter()

    for entry in data:
        meta = entry.get("metadata", {})
        for tag in meta.get("tags", []):
            tag_counter[tag] += 1
        for api in meta.get("key_apis", []):
            api_counter[api] += 1

    return {
        "total": total,
        "tag_distribution": dict(tag_counter.most_common()),
        "key_api_distribution": dict(api_counter.most_common()),
        "unique_tags": len(tag_counter),
        "unique_key_apis": len(api_counter),
    }


def print_code_index(result: dict):
    print_section("2. 代码范例库 (genesis_code_index.json)")
    print(f"\n  总代码范例数  : {result['total']:,}")
    print(f"  独立 Tag 种类 : {result['unique_tags']}")
    print(f"  独立 API 种类 : {result['unique_key_apis']}")

    print_counter(Counter(result["tag_distribution"]), "Tag 分布", TOP_N)
    print_counter(Counter(result["key_api_distribution"]), "Key-API 分布", TOP_N)


# ─────────────────────────── 3. 代码片段库 ───────────────────────────
def analyze_snippets(data: list) -> dict:
    total = len(data)
    tag_counter = Counter()
    api_counter = Counter()

    for entry in data:
        for tag in entry.get("tags", []):
            tag_counter[tag] += 1
        for api in entry.get("key_apis", []):
            api_counter[api] += 1

    # 手动添加 vs 自动提取
    manual_count = sum(1 for e in data if "manual_added" in e.get("tags", []))
    auto_count   = total - manual_count

    return {
        "total": total,
        "manual_added": manual_count,
        "auto_extracted": auto_count,
        "tag_distribution": dict(tag_counter.most_common()),
        "key_api_distribution": dict(api_counter.most_common()),
        "unique_tags": len(tag_counter),
        "unique_key_apis": len(api_counter),
    }


def print_snippets(result: dict):
    print_section("3. 代码片段库 (genesis_code_snippets.json)")
    print(f"\n  总片段数      : {result['total']:,}")
    print(f"  自动提取      : {result['auto_extracted']:,}")
    print(f"  手动添加      : {result['manual_added']:,}")
    print(f"  独立 Tag 种类 : {result['unique_tags']}")
    print(f"  独立 API 种类 : {result['unique_key_apis']}")

    print_counter(Counter(result["tag_distribution"]), "Tag 分布", TOP_N)
    print_counter(Counter(result["key_api_distribution"]), f"Key-API 分布（Top {TOP_N}，完整见 JSON）", TOP_N)


# ─────────────────────────── 主流程 ───────────────────────────
def main():
    print(f"\n{'#'*60}")
    print(f"  RAG 知识库健康度评估报告")
    print(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    # 加载数据
    print("\n正在加载知识库文件...")
    api_data      = load_json(KB_API)
    code_data     = load_json(KB_CODE)
    snippets_data = load_json(KB_SNIPPETS)
    print(f"  ✅ API 知识库    : {len(api_data):,} 条")
    print(f"  ✅ 代码范例库    : {len(code_data):,} 条")
    print(f"  ✅ 代码片段库    : {len(snippets_data):,} 条")

    # 分析
    api_result      = analyze_api_kb(api_data)
    code_result     = analyze_code_index(code_data)
    snippets_result = analyze_snippets(snippets_data)

    # 打印报告
    print_api_kb(api_result)
    print_code_index(code_result)
    print_snippets(snippets_result)

    # 综合摘要
    print_section("综合摘要")
    print(f"\n  {'指标':<35} {'值'}")
    print(f"  {'-'*35} {'-'*20}")
    print(f"  {'API 总条目':<35} {api_result['total']:,}")
    print(f"  {'API Summary 覆盖率':<35} {api_result['summary_coverage']['rate']*100:.1f}%")
    print(f"  {'API Constraints 覆盖率':<35} {api_result['constraints_coverage']['rate']*100:.1f}%")
    print(f"  {'Core API 数量':<35} {api_result['core_api_count']:,}")
    print(f"  {'代码范例总数':<35} {code_result['total']:,}")
    print(f"  {'代码范例 Tag 种类':<35} {code_result['unique_tags']}")
    print(f"  {'代码范例 Key-API 种类':<35} {code_result['unique_key_apis']}")
    print(f"  {'代码片段总数':<35} {snippets_result['total']:,}")
    print(f"  {'代码片段 Tag 种类':<35} {snippets_result['unique_tags']}")
    print(f"  {'代码片段 Key-API 种类':<35} {snippets_result['unique_key_apis']}")

    # 保存完整 JSON 报告
    full_report = {
        "generated_at": datetime.now().isoformat(),
        "api_knowledge_base": api_result,
        "code_index": code_result,
        "code_snippets": snippets_result,
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(full_report, f, ensure_ascii=False, indent=2)

    print(f"\n{'─'*60}")
    print(f"  ✅ 完整数据已保存至: {OUTPUT_JSON}")
    print(f"     （Tag / Key-API 完整排名请查阅该文件）")
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
把 newest/ 里某次 no-exec 召回跑批的 rag_hit 数据，按 task_id 合并进
对比执行结果（result.json），使执行结果同时携带"召回率"和"执行成功率"，
便于关联分析（高召回+低执行 = 生成问题；低召回+低执行 = 检索问题）。

用法：
  cd rag_demo/
  python benchmark/scripts/merge_recall.py \
      --exec benchmark/results/comparisons/rag_vs_no_rag_full/result.json \
      --recall benchmark/results/newest/08_hyde_unit_rerank-10/benchmark_20260609_165559.json

默认 --recall 自动找 newest/08_hyde_unit_rerank-10（与 Best RAG 配置最接近）。
原执行结果会备份为 *.exec_only.json，result.json 被原地更新（仅向 best_rag 任务
追加 rag_hit / context_length 字段，不改执行数据）。
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from collections import defaultdict


def _auto_find_recall_json() -> str:
    base = Path(__file__).resolve().parents[1] / "results" / "newest"
    d = base / "08_hyde_unit_rerank-10"
    cands = sorted(d.glob("benchmark_*.json")) if d.is_dir() else []
    cands = [c for c in cands if "miss" not in c.name]
    return str(cands[0]) if cands else ""


def main():
    ap = argparse.ArgumentParser(description="把召回率 rag_hit 合并进执行对比结果")
    ap.add_argument("--exec", required=True, help="对比执行结果 result.json")
    ap.add_argument("--recall", default=None, help="no-exec 召回跑批 JSON（默认自动找 newest/08_*）")
    ap.add_argument("--no-backup", action="store_true", help="不备份原执行结果")
    args = ap.parse_args()

    exec_path = args.exec
    recall_path = args.recall or _auto_find_recall_json()
    if not recall_path or not os.path.isfile(recall_path):
        print("未找到召回 JSON，请用 --recall 指定", file=sys.stderr)
        sys.exit(1)

    print("执行结果: {}".format(exec_path))
    print("召回来源: {}".format(recall_path))

    exe = json.load(open(exec_path, encoding="utf-8"))
    rec = json.load(open(recall_path, encoding="utf-8"))

    # 召回参数（用于记录合并来源）
    recall_params = rec.get("rag_search_params", {})

    # 建 task_id -> 召回数据 映射
    recall_map = {}
    for t in rec.get("tasks", []):
        tid = t.get("task_id")
        if not tid:
            continue
        recall_map[tid] = {
            "rag_hit": t.get("rag_hit"),
            "context_length_initial": t.get("context_length_initial"),
            "context_length_final": t.get("context_length_final"),
        }

    # 合并进 best_rag（No RAG 本就没有检索，不注入）
    merged_n = 0
    for ct in exe["tasks"].get("best_rag", []):
        tid = ct.get("task_id")
        if tid in recall_map:
            ct.update(recall_map[tid])
            merged_n += 1

    exe["recall_source"] = {
        "json": os.path.relpath(recall_path, Path(exec_path).resolve().parents[2]),
        "rag_search_params": recall_params,
        "merged_task_count": merged_n,
        "note": "rag_hit/context_length 来自 no-exec 召回跑批；检索量(n_api/n_units等)"
                "可能小于执行跑批的满配，召回率为保守近似",
    }

    # 备份原文件
    if not args.no_backup:
        bak = exec_path.replace(".json", ".exec_only.json")
        if not os.path.isfile(bak):
            shutil.copy2(exec_path, bak)
            print("原执行结果已备份: {}".format(bak))

    with open(exec_path, "w", encoding="utf-8") as f:
        json.dump(exe, f, indent=2, ensure_ascii=False)
    print("已合并 {}/{} 条 best_rag 任务的召回率".format(merged_n, len(exe["tasks"].get("best_rag", []))))

    # ── 关联分析 ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("  召回率 ↔ 执行成功率 关联分析（Best RAG, n={}）".format(merged_n))
    print("=" * 60)

    br = exe["tasks"].get("best_rag", [])
    # 分桶：高召回(>=0.7) vs 低召回(<0.7)，看各自的执行成功率
    hi, lo = [], []
    for t in br:
        rh = (t.get("rag_hit") or {}).get("hit_rate")
        if rh is None:
            continue
        (hi if rh >= 0.7 else lo).append(t)

    def _rate(lst, key):
        if not lst:
            return None
        return sum(1 for t in lst if t.get(key)) / len(lst)

    print("\n按召回率分桶:")
    for name, lst in [("高召回(>=0.7)", hi), ("低召回(<0.7)", lo)]:
        if lst:
            avg_rag = sum((t["rag_hit"].get("hit_rate") or 0) for t in lst) / len(lst)
            print("  {:<16} n={:>3}  平均召回={:.0%}  P@1={:.0%}  P@3={:.0%}".format(
                name, len(lst), avg_rag, _rate(lst, "pass_at_1") or 0, _rate(lst, "pass_at_3") or 0))

    # 四象限
    q = defaultdict(list)
    for t in br:
        rh = (t.get("rag_hit") or {}).get("hit_rate")
        p1 = t.get("pass_at_1")
        if rh is None or p1 is None:
            continue
        q[(rh >= 0.7, p1)].append(t["task_id"])

    print("\n四象限分布 (召回阈值0.7, P@1):")
    print("  高召回+P@1成功: {:>3}  ← RAG 完美发挥".format(len(q[(True, True)])))
    print("  高召回+P@1失败: {:>3}  ← 召回到但生成没用好（生成/执行问题）".format(len(q[(True, False)])))
    print("  低召回+P@1成功: {:>3}  ← 召回不足但侥幸成功".format(len(q[(False, True)])))
    print("  低召回+P@1失败: {:>3}  ← 召回不足导致失败（检索问题）".format(len(q[(False, False)])))

    if q[(True, False)]:
        print("\n高召回却失败的 task（生成瓶颈，值得关注）:")
        print("  " + ", ".join(q[(True, False)][:15]))
    if q[(False, False)]:
        print("\n低召回且失败的 task（检索瓶颈）:")
        print("  " + ", ".join(q[(False, False)][:15]))


if __name__ == "__main__":
    main()

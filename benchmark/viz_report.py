"""
benchmark/viz_report.py
=======================
将 benchmark JSON 结果渲染为单文件 HTML（Chart.js CDN），支持：

  - 单次 run：一张总览 + 逐任务表 + 可选复杂度/Domain 小图
  - 多次 run：对比柱状图 + 汇总表 + 逐任务跨实验热力对比
  - Tab 切换：📊 RAG 召回 / 🚀 执行成功率 / 📋 全部指标

用法见 visualize_benchmark.py；也可被 run_benchmark.py / run_benchmark_batch.py 调用。
"""

from __future__ import annotations

import html as html_module
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

PALETTE = [
    "#5b8def", "#7c6cf0", "#e07a5f", "#3d9970", "#ff851b",
    "#e84393", "#00cec9", "#fdcb6e", "#636e72", "#a29bfe",
]


def _pct(v: Any, digits: int = 1) -> str:
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        return f"{v * 100:.{digits}f}%"
    return "—"


def _num(v: Any, digits: int = 0) -> str:
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        return f"{v:,.{digits}f}".replace(",", "’") if digits else f"{int(v):,}"
    return "—"


def _short_label(
    data: Dict[str, Any],
    index: int,
    all_runs: Optional[List[Dict[str, Any]]] = None,
) -> str:
    all_runs = all_runs or [data]
    all_skip_exec = all(r.get("skip_execution") for r in all_runs)
    all_retries = {r.get("max_retries") for r in all_runs}
    hyde_routes: set = set()
    for r in all_runs:
        if r.get("rag_rewrite_mode") == "hyde":
            hr = (r.get("rag_search_params") or {}).get("hyde_route")
            if hr:
                hyde_routes.add(hr)

    parts: List[str] = []
    rw = data.get("rag_rewrite_mode", "none")
    if rw == "hyde":
        hr = (data.get("rag_search_params") or {}).get("hyde_route")
        if hr and len(hyde_routes) > 1:
            parts.append(f"hyde/{hr}")
        else:
            parts.append("hyde")
    else:
        parts.append(str(rw))

    rerank = (data.get("rag_search_params") or {}).get("rerank")
    if rerank:
        rtop = (data.get("rag_search_params") or {}).get("rerank_top_n")
        if rtop is not None:
            parts.append(f"rerank(top={rtop})")
        else:
            parts.append("+rerank")

    if data.get("skip_execution") and not all_skip_exec:
        parts.append("no-exec")
    if len(all_retries) > 1:
        mr = data.get("max_retries")
        if mr is not None:
            parts.append(f"retry={mr}")

    return f"#{index} {' '.join(parts)}"


def _summary_row(group: str, m: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "group": group,
        "n": m.get("n", 0),
        "rag_hit_rate": m.get("rag_hit_rate"),
        "unit_hit_rate": m.get("unit_hit_rate"),
        "avg_new_hit_rate": m.get("avg_new_hit_rate"),
        "avg_dynamic_slice_hit_rate": m.get("avg_dynamic_slice_hit_rate"),
        "avg_context_tokens_initial": m.get("avg_context_tokens_initial"),
        "avg_context_tokens_final": m.get("avg_context_tokens_final"),
        "pass_at_1": m.get("pass_at_1"),
        "pass_at_3": m.get("pass_at_3"),
    }


def _task_row(task: Dict[str, Any]) -> Dict[str, Any]:
    rag = task.get("rag_hit") or {}
    dyn = task.get("rag_hit_after_dynamic") or {}
    exe = task.get("execution") or {}
    inc = task.get("rag_incremental") or {}
    tok_i = (task.get("context_length_initial") or {}).get("total_tokens")
    tok_f = (task.get("context_length_final") or {}).get("total_tokens")
    if tok_f is None:
        tok_f = tok_i
    return {
        "task_id": task.get("task_id", ""),
        "complexity": task.get("complexity", ""),
        "domain": task.get("domain", ""),
        "query": (task.get("query") or "")[:200],
        "rag_hit_rate": rag.get("hit_rate"),
        "rag_unit_rate": rag.get("unit_hit_rate"),
        "dyn_hit_rate": dyn.get("hit_rate") if dyn else None,
        "dyn_unit_rate": dyn.get("unit_hit_rate") if dyn else None,
        "pass_at_1": exe.get("pass_at_1"),
        "pass_at_3": exe.get("pass_at_3"),
        "success_attempt": exe.get("success_attempt"),
        "new_hit_rate": inc.get("new_hit_rate") if isinstance(inc, dict) else None,
        "dynamic_item_count": inc.get("dynamic_item_count") if isinstance(inc, dict) else None,
        "tok_i": tok_i,
        "tok_f": tok_f,
        "duration_seconds": task.get("duration_seconds"),
    }


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _safe_json_for_script(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


# ─────────────────────────────────────────────────────────────
# HTML builder
# ─────────────────────────────────────────────────────────────

def build_html(
    runs: List[Tuple[str, Optional[str], Dict[str, Any]]],
    title: str = "Benchmark 可视化报告",
) -> str:
    """
    :param runs: [(label, json_path_or_none, data_dict), ...]
    """
    multi = len(runs) > 1

    # ---- chart payloads ----
    chart_payload = {
        "labels": [r[0] for r in runs],
        "rag": [],
        "unit": [],
        "new_hit": [],
        "dyn_slice": [],
        "p1": [],
        "p3": [],
        "tok_f": [],
    }
    for _, _, d in runs:
        s = d.get("summary") or {}
        o = s.get("overall") or {}
        chart_payload["rag"].append(o.get("rag_hit_rate"))
        chart_payload["unit"].append(o.get("unit_hit_rate"))
        chart_payload["new_hit"].append(o.get("avg_new_hit_rate"))
        chart_payload["dyn_slice"].append(o.get("avg_dynamic_slice_hit_rate"))
        chart_payload["p1"].append(o.get("pass_at_1"))
        chart_payload["p3"].append(o.get("pass_at_3"))
        chart_payload["tok_f"].append(o.get("avg_context_tokens_final"))

    # ---- per-task cross-run alignment ----
    task_ids: List[str] = []
    if runs:
        first_tasks = runs[0][2].get("tasks") or []
        task_ids = [t.get("task_id", "") for t in first_tasks if t.get("task_id")]

    matrix_rag: List[List[Optional[float]]] = []
    matrix_p1: List[List[Optional[bool]]] = []
    for _, _, d in runs:
        by_id = {t.get("task_id"): t for t in (d.get("tasks") or [])}
        row_r: List[Optional[float]] = []
        row_p: List[Optional[bool]] = []
        for tid in task_ids:
            t = by_id.get(tid)
            if not t:
                row_r.append(None)
                row_p.append(None)
                continue
            rag = t.get("rag_hit") or {}
            exe = t.get("execution") or {}
            row_r.append(rag.get("hit_rate") if isinstance(rag.get("hit_rate"), (int, float)) else None)
            row_p.append(exe.get("pass_at_1") if exe else None)
        matrix_rag.append(row_r)
        matrix_p1.append(row_p)

    # ---- domain aggregation ----
    domain_labels: List[str] = []
    domain_datasets: List[dict] = []
    if runs:
        domain_set: set = set()
        for t in (runs[0][2].get("tasks") or []):
            dom = t.get("domain")
            if dom:
                domain_set.add(dom)
        domain_labels = sorted(domain_set)
        for ci, (label, _, d) in enumerate(runs):
            tasks = d.get("tasks") or []
            by_dom: Dict[str, List[float]] = {dom: [] for dom in domain_labels}
            for t in tasks:
                dom = t.get("domain")
                if not dom or dom not in by_dom:
                    continue
                rag = t.get("rag_hit") or {}
                hr = rag.get("hit_rate")
                if isinstance(hr, (int, float)):
                    by_dom[dom].append(float(hr))
            vals = [
                round(sum(vs) / len(vs), 4) if vs else None
                for vs in [by_dom[d] for d in domain_labels]
            ]
            c = PALETTE[ci % len(PALETTE)]
            domain_datasets.append({
                "label": label,
                "data": vals,
                "backgroundColor": c + "cc",
                "borderColor": c,
                "borderWidth": 1,
            })

    # ---- detect if any run has execution data ----
    has_exec = any(
        any(
            (t.get("execution") or {}).get("pass_at_1") is not None
            for t in (d.get("tasks") or [])
        )
        for _, _, d in runs
    )

    # ---- per-run sections ----
    per_run_sections: List[str] = []
    for idx, (label, jpath, d) in enumerate(runs, start=1):
        summary = d.get("summary") or {}
        meta_bits = [
            f"run_id: {html_module.escape(str(d.get('run_id', '')))}",
            f"timestamp: {html_module.escape(str(d.get('timestamp', '')))}",
            f"tasks: {d.get('task_count', '—')}",
        ]
        if jpath:
            p = Path(jpath)
            short_path = f"{p.parent.name}/{p.name}"
            meta_bits.append(f"file: {html_module.escape(short_path)}")
        groups = ["overall", "simple", "medium", "hard"]
        sum_rows = [_summary_row(g, summary.get(g) or {}) for g in groups if (summary.get(g) or {}).get("n")]

        sum_table = ""
        if sum_rows:
            sum_table = (
                "<table class='data'><thead><tr>"
                "<th>组别</th><th>N</th>"
                "<th class='col-rag'>RAG</th><th class='col-rag'>语义</th>"
                "<th class='col-rag'>新增命中</th><th class='col-rag'>dyn子集</th>"
                "<th class='col-rag'>TokI</th><th class='col-rag'>TokF</th>"
                "<th class='col-exec'>P@1</th><th class='col-exec'>P@3</th>"
                "</tr></thead><tbody>"
            )
            for row in sum_rows:
                sum_table += (
                    f"<tr><td>{html_module.escape(str(row['group']))}</td>"
                    f"<td>{row['n']}</td>"
                    f"<td class='col-rag'>{_pct(row['rag_hit_rate'])}</td>"
                    f"<td class='col-rag'>{_pct(row['unit_hit_rate'])}</td>"
                    f"<td class='col-rag'>{_pct(row['avg_new_hit_rate']) if row.get('avg_new_hit_rate') is not None else '—'}</td>"
                    f"<td class='col-rag'>{_pct(row['avg_dynamic_slice_hit_rate']) if row.get('avg_dynamic_slice_hit_rate') is not None else '—'}</td>"
                    f"<td class='col-rag'>{_num(row['avg_context_tokens_initial'], 0)}</td>"
                    f"<td class='col-rag'>{_num(row['avg_context_tokens_final'], 0)}</td>"
                    f"<td class='col-exec'>{_pct(row['pass_at_1'])}</td>"
                    f"<td class='col-exec'>{_pct(row['pass_at_3'])}</td></tr>"
                )
            sum_table += "</tbody></table>"

        tasks = d.get("tasks") or []
        task_rows_html = ""
        for t in tasks:
            tr = _task_row(t)
            q = html_module.escape(tr["query"])
            task_rows_html += (
                f"<tr><td class='mono'>{html_module.escape(tr['task_id'])}</td>"
                f"<td><span class='tag {tr['complexity']}'>{html_module.escape(tr['complexity'])}</span></td>"
                f"<td class='query' title='{q}'>{q}{'…' if len(tr['query']) >= 200 else ''}</td>"
                f"<td class='col-rag'>{_pct(tr['rag_hit_rate'])}</td>"
                f"<td class='col-rag'>{_pct(tr['dyn_hit_rate']) if tr['dyn_hit_rate'] is not None else '—'}</td>"
                f"<td class='col-rag'>{_pct(tr['new_hit_rate']) if tr['new_hit_rate'] is not None else '—'}</td>"
                f"<td class='col-exec'>{'✓' if tr['pass_at_1'] else '✗' if tr['pass_at_1'] is not None else '—'}</td>"
                f"<td class='col-exec'>{'✓' if tr['pass_at_3'] else '✗' if tr['pass_at_3'] is not None else '—'}</td>"
                f"<td class='col-rag'>{_num(tr['tok_i'], 0)}/{_num(tr['tok_f'], 0)}</td>"
                f"<td class='col-exec'>{tr.get('duration_seconds', '—')}</td></tr>"
            )

        rerank_on = (d.get("rag_search_params") or {}).get("rerank")
        rerank_badge = ' <span class="badge-rerank">+rerank</span>' if rerank_on else ""

        per_run_sections.append(
            f"<section class='card run-detail' id='run-{idx}'>"
            f"<h2>{html_module.escape(label)}{rerank_badge}</h2>"
            f"<p class='meta'>{' · '.join(meta_bits)}</p>"
            f"{sum_table}"
            f"<h3>逐任务</h3><div class='table-wrap'><table class='data tasks'>"
            "<thead><tr><th>task</th><th>cx</th><th>query</th>"
            "<th class='col-rag'>RAG</th><th class='col-rag'>Dynamic</th>"
            "<th class='col-rag'>新增命中</th>"
            "<th class='col-exec'>P@1</th><th class='col-exec'>P@3</th>"
            "<th class='col-rag'>Tok I/F</th><th class='col-exec'>sec</th></tr></thead>"
            f"<tbody>{task_rows_html}</tbody></table></div></section>"
        )

    # ---- cross-task heatmap tables (multi-run) ----
    def _th_cls(d: dict) -> str:
        return ' class="col-rerank"' if (d.get("rag_search_params") or {}).get("rerank") else ""

    heat_rag_html = ""
    heat_exec_html = ""
    if multi and task_ids:
        # RAG heatmap
        heat_rag_html = (
            "<section class='card section-rag'><h2>逐任务 RAG 命中率（跨实验对比）</h2>"
            "<div class='table-wrap'><table class='data heatmap'>"
            "<thead><tr><th>task_id</th>" + "".join(
                f"<th{_th_cls(d)}>{html_module.escape(l)}</th>"
                for l, _, d in runs
            ) + "</tr></thead><tbody>"
        )
        for i, tid in enumerate(task_ids):
            heat_rag_html += f"<tr><td class='mono'>{html_module.escape(tid)}</td>"
            for ri, _ in enumerate(runs):
                v = matrix_rag[ri][i] if ri < len(matrix_rag) and i < len(matrix_rag[ri]) else None
                if v is None:
                    heat_rag_html += "<td class='na'>—</td>"
                else:
                    pct_val = v * 100
                    alpha = min(1.0, max(0.15, pct_val / 100))
                    heat_rag_html += (
                        f"<td style='--a:{alpha:.2f}' class='cell'><span>{pct_val:.0f}%</span></td>"
                    )
            heat_rag_html += "</tr>"
        heat_rag_html += "</tbody></table></div></section>"

        # Pass@1 heatmap
        heat_exec_html = (
            "<section class='card section-exec'><h2>Pass@1（跨实验对比）</h2>"
            "<div class='table-wrap'><table class='data'>"
            "<thead><tr><th>task_id</th>" + "".join(
                f"<th{_th_cls(d)}>{html_module.escape(l)}</th>"
                for l, _, d in runs
            ) + "</tr></thead><tbody>"
        )
        for i, tid in enumerate(task_ids):
            heat_exec_html += f"<tr><td class='mono'>{html_module.escape(tid)}</td>"
            for ri, _ in enumerate(runs):
                p = matrix_p1[ri][i] if ri < len(matrix_p1) and i < len(matrix_p1[ri]) else None
                if p is True:
                    heat_exec_html += "<td class='ok'>✓</td>"
                elif p is False:
                    heat_exec_html += "<td class='bad'>✗</td>"
                else:
                    heat_exec_html += "<td>—</td>"
            heat_exec_html += "</tr>"
        heat_exec_html += "</tbody></table></div></section>"

    # ---- comparison blocks (multi-run) ----
    compare_rag_html = ""
    compare_exec_html = ""
    compare_all_html = ""
    if multi:
        # RAG-only comparison
        compare_rag_html = (
            "<section class='card section-rag'><h2>RAG 召回对比（Overall）</h2>"
            "<canvas id='chartCompareRAG' height='120'></canvas>"
            "<div class='table-wrap'><table class='data'><thead><tr>"
            "<th>实验</th><th>RAG</th><th>语义RAG</th><th>新增命中</th><th>dyn子集</th><th>TokF</th></tr></thead><tbody>"
        )
        for label, _, d in runs:
            o = (d.get("summary") or {}).get("overall") or {}
            compare_rag_html += (
                f"<tr><td>{html_module.escape(label)}</td>"
                f"<td>{_pct(o.get('rag_hit_rate'))}</td>"
                f"<td>{_pct(o.get('unit_hit_rate'))}</td>"
                f"<td>{_pct(o.get('avg_new_hit_rate')) if o.get('avg_new_hit_rate') is not None else '—'}</td>"
                f"<td>{_pct(o.get('avg_dynamic_slice_hit_rate')) if o.get('avg_dynamic_slice_hit_rate') is not None else '—'}</td>"
                f"<td>{_num(o.get('avg_context_tokens_final'), 0)}</td></tr>"
            )
        compare_rag_html += "</tbody></table></div></section>"

        # Exec-only comparison
        compare_exec_html = (
            "<section class='card section-exec'><h2>执行成功率对比（Overall）</h2>"
        )
        if has_exec:
            compare_exec_html += (
                "<canvas id='chartCompareExec' height='120'></canvas>"
                "<div class='table-wrap'><table class='data'><thead><tr>"
                "<th>实验</th><th>Pass@1</th><th>Pass@3</th></tr></thead><tbody>"
            )
            for label, _, d in runs:
                o = (d.get("summary") or {}).get("overall") or {}
                compare_exec_html += (
                    f"<tr><td>{html_module.escape(label)}</td>"
                    f"<td>{_pct(o.get('pass_at_1'))}</td>"
                    f"<td>{_pct(o.get('pass_at_3'))}</td></tr>"
                )
            compare_exec_html += "</tbody></table></div>"
        else:
            compare_exec_html += (
                "<div class='empty-hint'>本次实验均未开启代码执行（--no-exec），无 Pass@1 / Pass@3 数据。</div>"
            )
        compare_exec_html += "</section>"

        # All-in-one comparison
        compare_all_html = (
            "<section class='card section-all'><h2>全部指标对比（Overall）</h2>"
            "<canvas id='chartCompareAll' height='120'></canvas>"
            "<div class='table-wrap'><table class='data'><thead><tr>"
            "<th>实验</th><th>RAG</th><th>语义RAG</th><th>新增命中</th><th>dyn子集</th>"
            "<th>P@1</th><th>P@3</th><th>TokF</th></tr></thead><tbody>"
        )
        for label, _, d in runs:
            o = (d.get("summary") or {}).get("overall") or {}
            compare_all_html += (
                f"<tr><td>{html_module.escape(label)}</td>"
                f"<td>{_pct(o.get('rag_hit_rate'))}</td>"
                f"<td>{_pct(o.get('unit_hit_rate'))}</td>"
                f"<td>{_pct(o.get('avg_new_hit_rate')) if o.get('avg_new_hit_rate') is not None else '—'}</td>"
                f"<td>{_pct(o.get('avg_dynamic_slice_hit_rate')) if o.get('avg_dynamic_slice_hit_rate') is not None else '—'}</td>"
                f"<td>{_pct(o.get('pass_at_1'))}</td>"
                f"<td>{_pct(o.get('pass_at_3'))}</td>"
                f"<td>{_num(o.get('avg_context_tokens_final'), 0)}</td></tr>"
            )
        compare_all_html += "</tbody></table></div></section>"

    # ---- complexity chart (RAG tab) ----
    complexity_chart_html = ""
    if runs:
        complexity_chart_html = (
            "<section class='card section-rag'><h2>按难度分组的 RAG 总召回</h2>"
            "<canvas id='chartByComplexity' height='100'></canvas></section>"
        )

    # ---- domain chart (RAG tab) ----
    domain_chart_html = ""
    if domain_labels:
        domain_chart_html = (
            "<section class='card section-rag'><h2>按 Domain 分组的 RAG 命中率</h2>"
            "<canvas id='chartByDomain' height='100'></canvas></section>"
        )

    # ---- serialize chart data ----
    chart_json = _safe_json_for_script(chart_payload)
    cx_labels = ["simple", "medium", "hard"]
    cx_datasets = []
    for ci, (label, _, d) in enumerate(runs):
        summary = d.get("summary") or {}
        vals = []
        for g in cx_labels:
            m = summary.get(g) or {}
            v = m.get("rag_hit_rate")
            vals.append(float(v) if isinstance(v, (int, float)) else None)
        c = PALETTE[ci % len(PALETTE)]
        cx_datasets.append({
            "label": label,
            "data": vals,
            "backgroundColor": c + "cc",
            "borderColor": c,
            "borderWidth": 1,
        })
    cx_json = _safe_json_for_script({"labels": cx_labels, "datasets": cx_datasets})
    domain_json = _safe_json_for_script({"labels": domain_labels, "datasets": domain_datasets})

    now = datetime.now().isoformat(timespec="seconds")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{html_module.escape(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #0f1219; --surface: #171b24; --card: #1c2130;
      --border: #2a3142; --text: #e8eaef; --muted: #8b93a7;
      --accent: #6c9eff; --good: #3ecf8e; --bad: #f07178;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; font-family: 'DM Sans', system-ui, sans-serif;
      background: var(--bg); color: var(--text);
      line-height: 1.5; padding: 2rem 1.5rem 4rem;
    }}
    .wrap {{ max-width: 1200px; margin: 0 auto; }}
    header {{
      margin-bottom: 1.5rem; padding-bottom: 1.25rem;
      border-bottom: 1px solid var(--border);
    }}
    h1 {{ font-size: 1.75rem; font-weight: 700; margin: 0 0 0.5rem; letter-spacing: -0.02em; }}
    .sub {{ color: var(--muted); font-size: 0.95rem; }}
    .card {{
      background: var(--card); border: 1px solid var(--border);
      border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;
      box-shadow: 0 4px 24px rgba(0,0,0,.25);
    }}
    h2 {{ font-size: 1.15rem; margin: 0 0 1rem; color: var(--accent); font-weight: 600; }}
    h3 {{ font-size: 1rem; margin: 1.25rem 0 0.75rem; color: var(--muted); }}
    .meta {{ font-size: 0.8rem; color: var(--muted); font-family: 'JetBrains Mono', monospace; margin-bottom: 1rem; }}
    .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
    table.data {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    table.data th, table.data td {{
      padding: 0.5rem 0.65rem; text-align: left; border-bottom: 1px solid var(--border);
    }}
    table.data th {{ color: var(--muted); font-weight: 600; white-space: nowrap; }}
    table.data tr:hover td {{ background: rgba(255,255,255,.03); }}
    td.mono {{ font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; }}
    td.query {{ max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .tag {{
      display: inline-block; padding: 0.15rem 0.45rem; border-radius: 6px;
      font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
    }}
    .tag.simple {{ background: #1e3a2f; color: #3ecf8e; }}
    .tag.medium {{ background: #3a2e1e; color: #ffb347; }}
    .tag.hard {{ background: #3a1e2e; color: #ff8cc8; }}
    table.heatmap td.cell {{
      background: rgba(108, 158, 255, var(--a, 0.5)); text-align: center;
      font-weight: 600; font-size: 0.8rem;
    }}
    table.heatmap td.na {{ color: var(--muted); text-align: center; }}
    td.ok {{ color: var(--good); text-align: center; font-weight: 700; }}
    td.bad {{ color: var(--bad); text-align: center; font-weight: 700; }}
    canvas {{ max-height: 320px !important; }}
    .toc {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem; }}
    .toc a {{
      color: var(--accent); text-decoration: none; font-size: 0.85rem;
      padding: 0.35rem 0.75rem; border: 1px solid var(--border); border-radius: 8px;
    }}
    .toc a:hover {{ background: var(--surface); }}
    .badge-rerank {{
      display: inline-block; padding: 0.15rem 0.5rem; border-radius: 6px;
      font-size: 0.7rem; font-weight: 600; background: #1e2a3a; color: #6c9eff;
      margin-left: 0.5rem; vertical-align: middle;
    }}
    th.col-rerank {{ background: rgba(108, 158, 255, 0.12); }}

    /* ===== Tab system ===== */
    .tab-bar {{
      display: flex; gap: 8px; margin-bottom: 1.5rem;
      padding: 6px; background: var(--surface); border-radius: 10px; border: 1px solid var(--border);
    }}
    .tab-btn {{
      padding: 8px 22px; border: 1px solid transparent; border-radius: 8px;
      background: transparent; color: var(--muted); cursor: pointer;
      font-size: 0.9rem; font-family: inherit; font-weight: 500;
      transition: all 0.2s;
    }}
    .tab-btn:hover {{ color: var(--text); background: var(--card); }}
    .tab-btn.active {{
      background: var(--accent); color: #fff; border-color: var(--accent);
      box-shadow: 0 2px 8px rgba(108,158,255,0.3);
    }}
    /* Section visibility */
    .section-rag, .section-exec, .section-all {{ display: block; }}
    body.tab-rag .section-exec {{ display: none; }}
    body.tab-rag .section-all {{ display: none; }}
    body.tab-exec .section-rag {{ display: none; }}
    body.tab-exec .section-all {{ display: none; }}
    body.tab-all .section-rag {{ display: block; }}
    body.tab-all .section-exec {{ display: block; }}
    /* Column visibility */
    body.tab-rag .col-exec {{ display: none; }}
    body.tab-exec .col-rag {{ display: none; }}
    /* Empty hint */
    .empty-hint {{
      padding: 2rem; text-align: center; color: var(--muted);
      font-size: 0.95rem; border: 1px dashed var(--border); border-radius: 8px;
    }}
    footer {{ margin-top: 3rem; color: var(--muted); font-size: 0.8rem; text-align: center; }}
  </style>
</head>
<body class="tab-rag">
  <div class="wrap">
    <header>
      <h1>{html_module.escape(title)}</h1>
      <p class="sub">生成时间 {html_module.escape(now)} · 共 {len(runs)} 次实验</p>
      <div class="tab-bar">
        <button class="tab-btn active" data-target="rag">📊 RAG 召回</button>
        <button class="tab-btn" data-target="exec">🚀 执行成功率</button>
        <button class="tab-btn" data-target="all">📋 全部指标</button>
      </div>
      <nav class="toc">
        {" ".join(f'<a href="#run-{i+1}">实验 {i+1}</a>' for i in range(len(runs)))}
      </nav>
    </header>
    {compare_rag_html}
    {compare_exec_html}
    {compare_all_html}
    {heat_rag_html}
    {heat_exec_html}
    {complexity_chart_html}
    {domain_chart_html}
    {"".join(per_run_sections)}
    <footer>rag_demo benchmark · visualize_benchmark</footer>
  </div>
  <script>
    const chartData = {chart_json};
    const cxData = {cx_json};
    const domainData = {domain_json};

    // ---- Tab switching ----
    document.querySelectorAll('.tab-btn').forEach(btn => {{
      btn.onclick = () => {{
        document.body.className = 'tab-' + btn.dataset.target;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      }};
    }});

    // ---- null-safe pct for charts ----
    const pct = (v) => v == null ? null : v * 100;

    // ---- Chart options template ----
    const chartOpts = (titleText) => ({{
      responsive: true,
      plugins: {{
        legend: {{ position: 'bottom', labels: {{ color: '#8b93a7' }} }},
        title: titleText ? {{ display: true, text: titleText, color: '#8b93a7' }} : {{ display: false }}
      }},
      scales: {{
        x: {{ ticks: {{ color: '#8b93a7', maxRotation: 45, minRotation: 0 }} }},
        y: {{
          beginAtZero: true, max: 100,
          ticks: {{ color: '#8b93a7', callback: v => v + '%' }}
        }}
      }}
    }});

    // ---- RAG comparison chart ----
    if (document.getElementById('chartCompareRAG')) {{
      new Chart(document.getElementById('chartCompareRAG').getContext('2d'), {{
        type: 'bar',
        data: {{
          labels: chartData.labels,
          datasets: [
            {{ label: 'RAG 总召回', data: chartData.rag.map(pct), backgroundColor: 'rgba(108,158,255,0.75)', spanGaps: true }},
            {{ label: '语义 RAG', data: chartData.unit.map(pct), backgroundColor: 'rgba(124,108,240,0.75)', spanGaps: true }},
          ]
        }},
        options: chartOpts()
      }});
    }}

    // ---- Exec comparison chart ----
    if (document.getElementById('chartCompareExec')) {{
      new Chart(document.getElementById('chartCompareExec').getContext('2d'), {{
        type: 'bar',
        data: {{
          labels: chartData.labels,
          datasets: [
            {{ label: 'Pass@1', data: chartData.p1.map(pct), backgroundColor: 'rgba(61,153,112,0.75)', spanGaps: true }},
            {{ label: 'Pass@3', data: chartData.p3.map(pct), backgroundColor: 'rgba(224,122,95,0.75)', spanGaps: true }},
          ]
        }},
        options: chartOpts()
      }});
    }}

    // ---- All-in-one comparison chart ----
    if (document.getElementById('chartCompareAll')) {{
      new Chart(document.getElementById('chartCompareAll').getContext('2d'), {{
        type: 'bar',
        data: {{
          labels: chartData.labels,
          datasets: [
            {{ label: 'RAG 总召回', data: chartData.rag.map(pct), backgroundColor: 'rgba(108,158,255,0.75)', spanGaps: true }},
            {{ label: '语义 RAG', data: chartData.unit.map(pct), backgroundColor: 'rgba(124,108,240,0.75)', spanGaps: true }},
            {{ label: 'Pass@1', data: chartData.p1.map(pct), backgroundColor: 'rgba(61,153,112,0.75)', spanGaps: true }},
            {{ label: 'Pass@3', data: chartData.p3.map(pct), backgroundColor: 'rgba(224,122,95,0.75)', spanGaps: true }},
          ]
        }},
        options: chartOpts()
      }});
    }}

    // ---- Complexity chart ----
    if (document.getElementById('chartByComplexity')) {{
      new Chart(document.getElementById('chartByComplexity').getContext('2d'), {{
        type: 'bar',
        data: {{
          labels: cxData.labels,
          datasets: cxData.datasets.map(ds => ({{
            ...ds,
            data: ds.data.map(v => v == null ? null : v * 100)
          }}))
        }},
        options: {{
          ...chartOpts(),
          plugins: {{
            legend: {{ position: 'bottom', labels: {{ color: '#8b93a7' }} }},
            tooltip: {{ callbacks: {{ label: c => c.dataset.label + ': ' + (c.raw == null ? 'N/A' : c.raw.toFixed(1) + '%') }} }}
          }}
        }}
      }});
    }}

    // ---- Domain chart ----
    if (document.getElementById('chartByDomain')) {{
      new Chart(document.getElementById('chartByDomain').getContext('2d'), {{
        type: 'bar',
        data: {{
          labels: domainData.labels,
          datasets: domainData.datasets.map(ds => ({{
            ...ds,
            data: ds.data.map(v => v == null ? null : v * 100)
          }}))
        }},
        options: {{
          ...chartOpts(),
          plugins: {{
            legend: {{ position: 'bottom', labels: {{ color: '#8b93a7' }} }},
            tooltip: {{ callbacks: {{ label: c => c.dataset.label + ': ' + (c.raw == null ? 'N/A' : c.raw.toFixed(1) + '%') }} }}
          }}
        }}
      }});
    }}
  </script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def write_benchmark_html(
    json_paths: List[str],
    output_path: Optional[str] = None,
    title: Optional[str] = None,
) -> str:
    """
    读取一个或多个 benchmark_*.json，写出单个 HTML 文件。
    :return: 输出文件的绝对路径字符串
    """
    paths = [Path(p).resolve() for p in json_paths]
    all_data = [_load_json(p) for p in paths]
    runs: List[Tuple[str, Optional[str], Dict[str, Any]]] = []
    for i, p in enumerate(paths):
        label = _short_label(all_data[i], i + 1, all_data)
        runs.append((label, str(p), all_data[i]))

    out = Path(output_path) if output_path else paths[0].parent / "benchmark_viz.html"
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    ttl = title or ("Benchmark 报告 · 单次" if len(runs) == 1 else f"Benchmark 对比 · {len(runs)} 次实验")
    html = build_html(runs, title=ttl)
    out.write_text(html, encoding="utf-8")
    return str(out)


def pick_main_benchmark_json(run_dir: Path) -> Optional[Path]:
    """
    在目录中选取「主」benchmark_*.json。

    `run_benchmark` 跑完后会再生成 `benchmark_miss_*.json` 等副产物，若按 mtime
    取最新文件会错选 miss 报告，导致可视化与 manifest 中无有效 overall/tasks 数据。
    """
    all_json = list(run_dir.glob("benchmark_*.json"))
    primary = [p for p in all_json if not p.name.startswith("benchmark_miss_")]
    cands = primary if primary else all_json
    if not cands:
        return None
    return max(cands, key=lambda p: p.stat().st_mtime)


def _coerce_to_main_benchmark_json_path(path: str) -> str:
    """若指向 benchmark_miss_*.json，则尽量换为同目录主结果文件。"""
    p = Path(path)
    if not p.is_file():
        return path
    if p.name.startswith("benchmark_miss_"):
        main = pick_main_benchmark_json(p.parent)
        if main is not None and main.is_file():
            return str(main.resolve())
    return str(p.resolve())


def load_manifest(manifest_path: str) -> List[str]:
    """从 batch manifest JSON 读取 json 文件路径列表（跳过缺失，并归一到主结果 JSON）。"""
    mp = Path(manifest_path).resolve()
    with open(mp, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    out: List[str] = []
    for entry in manifest:
        jp = entry.get("json") or entry.get("result_json")
        if jp and Path(jp).is_file():
            out.append(_coerce_to_main_benchmark_json_path(jp))
    return out

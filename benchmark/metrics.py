"""
benchmark/metrics.py
====================
评估指标计算工具。

两类核心指标：
  1. RAG Hit Rate  — 初始 RAG 检索结果是否覆盖了 expected_apis
  2. Pass@k        — 代码在前 k 次尝试内是否执行成功
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional

import os
import re
import threading

# tiktoken 可选；没有时使用近似方式估算 token
try:
    import tiktoken
except ImportError:
    tiktoken = None

# 首次 get_encoding("cl100k_base") 会从公网拉取 BPE 文件，离线/极慢时会出现长时间无输出。
# 这里做一次性、带超时的懒加载，超时则本进程内退回启发式，避免 benchmark「卡住」。
_cl100k_encoding: Any = None
_cl100k_encoding_tried: bool = False

# genesis 包顶层再导出 → 知识库 api_id 常用前缀（与 rag_demo 中逻辑保持一致，避免跨仓库依赖）
_GENESIS_PUBLIC_TO_CANONICAL_PREFIXES: tuple[tuple[str, str], ...] = (
    ("genesis.morphs.", "genesis.options.morphs."),
    ("genesis.sensors.", "genesis.options.sensors."),
    ("genesis.renderers.", "genesis.options.renderers."),
    ("genesis.surfaces.", "genesis.options.surfaces."),
    ("genesis.textures.", "genesis.options.textures."),
)


def normalize_api_id_for_kb(api_id: str) -> str:
    """将 genesis.morphs.* 等公开路径映射为 genesis.options.* 规范前缀，便于与 KB / 索引对齐。"""
    if not api_id or not api_id.startswith("genesis."):
        return api_id
    for public, canonical in _GENESIS_PUBLIC_TO_CANONICAL_PREFIXES:
        if api_id.startswith(public):
            return canonical + api_id[len(public) :]
    return api_id


def _add_api_match_forms(target: set, api: str) -> None:
    """同时收录原始、归一化、小写形式，兼容旧索引与 query 中的大小写不一致。"""
    api = api.strip()
    if not api:
        return
    target.add(api)
    target.add(api.lower())
    target.add(normalize_api_id_for_kb(api))


# ─────────────────────────────────────────────────────────────
# RAG 指标
# ─────────────────────────────────────────────────────────────

def compute_rag_hit(rag_context: List[dict], expected_apis: List[str]) -> dict:
    """
    计算 RAG 召回率，并区分命中来源。

    HyDE 模式下 context 包含两类 item，命中机制不同：
      - type="unit"  知识单元：优先通过 meta["all_apis"]（逗号字符串）精确匹配；
                     若旧数据无 all_apis，则回退到 meta["key_apis"]。
      - type="api"   既可能是 Core API 固定注入，也可能是 API 语义检索结果：
                     通过 content 前缀区分：
                       "--- CORE API:" -> core
                       "--- API:"      -> 语义检索（按 unit 口径计）

    per_api 的 source 字段：
      "semantic" — 语义检索命中（更有意义）
      "core"  — Core API 固定注入命中
      "miss"  — 未命中

    :param rag_context: ctx.data["meta"]["initial_rag_knowledge"]
    :param expected_apis: query.json 中的 expected_apis
    :return: {
        "per_api":         {"genesis.morphs.Sphere": {"hit": True, "source": "semantic"}, ...},
        "hit_count":       int,   # 总命中数（semantic + core）
        "unit_hit_count":  int,   # 语义检索命中数（衡量检索质量的核心指标）
        "core_hit_count":  int,   # 固定注入命中数
        "total":           int,
        "hit_rate":        float, # 总命中率
        "unit_hit_rate":   float, # 语义检索命中率（更能反映 RAG 检索质量）
    }
    """
    if not expected_apis:
        return {
            "per_api": {}, "hit_count": 0, "unit_hit_count": 0,
            "core_hit_count": 0, "total": 0, "hit_rate": 1.0, "unit_hit_rate": 1.0,
        }

    # 从各类 item 的 meta 中收集精确 api_id，区分来源
    unit_api_ids: set = set()
    core_api_ids: set = set()

    for item in rag_context:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type", "")
        meta      = item.get("meta", {}) or {}

        if item_type == "unit":
            # 新版优先 all_apis；旧版回退 key_apis
            unit_api_str = meta.get("all_apis", "") or meta.get("key_apis", "")
            for api in unit_api_str.split(","):
                _add_api_match_forms(unit_api_ids, api)

        elif item_type == "api":
            api_id = meta.get("api_id", "").strip()
            if api_id:
                # 最小修正：同为 type="api"，用 content 前缀区分 core 注入 vs API 语义检索
                # - "--- CORE API:"：固定注入，计入 core
                # - "--- API:"     ：语义检索，计入 semantic（避免 none 模式语义召回被错误记为 0）
                content = (item.get("content") or "").strip()
                if content.startswith("--- CORE API:"):
                    _add_api_match_forms(core_api_ids, api_id)
                else:
                    _add_api_match_forms(unit_api_ids, api_id)

        elif item_type in ("code", "snippet"):
            # 从 content 中用正则提取 genesis.* 调用模式，计入语义命中
            content = (item.get("content") or "")
            for m in re.finditer(r'(genesis\.\w+(?:\.\w+)*)', content):
                _add_api_match_forms(unit_api_ids, m.group(1))

    # 逐个判断命中
    per_api: Dict[str, dict] = {}
    for api in expected_apis:
        exp = normalize_api_id_for_kb(api)
        in_unit = exp in unit_api_ids or api in unit_api_ids or exp.lower() in unit_api_ids
        in_core = exp in core_api_ids or api in core_api_ids or exp.lower() in core_api_ids
        per_api[api] = {
            "hit":    in_unit or in_core,
            "source": "semantic" if in_unit else ("core" if in_core else "miss"),
        }

    hit_count      = sum(1 for v in per_api.values() if v["hit"])
    # 兼容历史结果：旧版 source 使用 "unit"，新版为 "semantic"
    unit_hit_count = sum(
        1 for v in per_api.values() if v["source"] in {"semantic", "unit"}
    )
    core_hit_count = sum(1 for v in per_api.values() if v["source"] == "core")
    total = len(expected_apis)

    return {
        "per_api":        per_api,
        "hit_count":      hit_count,
        "unit_hit_count": unit_hit_count,
        "core_hit_count": core_hit_count,
        "total":          total,
        "hit_rate":       round(hit_count      / total, 4),
        "unit_hit_rate":  round(unit_hit_count / total, 4),
    }


def knowledge_item_key(item: Any) -> str:
    """
    与 agents/critic.py 中动态 RAG 合并去重逻辑一致，用于区分「首轮已有」与「动态新增」条目。
    """
    if isinstance(item, dict):
        api_id = item.get("api_id") or (item.get("meta") or {}).get("api_id")
        if api_id:
            return str(api_id)
        typ = item.get("type", "") or ""
        content = item.get("content", "") or ""
        return typ + "|" + content[:200]
    return str(item)


def split_dynamic_knowledge(initial: List[dict], final: List[dict]) -> List[dict]:
    """
    final 相对 initial 多出的知识条目（动态 RAG 追加部分），顺序保持 final 中先后。
    与 critic 合并逻辑一致：同一 fingerprint 在首轮已存在则视为非新增；final 内重复键只保留第一条新增。
    """
    initial = initial or []
    final = final or []
    initial_keys = {
        knowledge_item_key(x) for x in initial if isinstance(x, dict)
    }
    out: List[dict] = []
    seen_new: set = set()
    for item in final:
        if not isinstance(item, dict):
            continue
        k = knowledge_item_key(item)
        if k in initial_keys or k in seen_new:
            continue
        seen_new.add(k)
        out.append(item)
    return out


def compute_rag_incremental_metrics(
    initial_context: List[dict],
    final_context: List[dict],
    expected_apis: List[str],
) -> dict:
    """
    动态 RAG 场景：最终 task_view = 首轮 initial_rag_knowledge + 动态追加（与 critic 合并逻辑一致）。

    「新增命中率」定义：在首轮检索未覆盖的 expected_apis 中，合并后新命中了多少比例。

      missed_initial = |{a ∈ expected : 首轮未命中 a}|
      recovered      = |{a ∈ expected : 首轮未命中 a 且 最终命中 a}|
      new_hit_rate   = recovered / missed_initial   （missed_initial=0 时为 None，表示无缺口可补）

    另提供 dynamic_slice：仅对「动态新增条目」子集做 compute_rag_hit，衡量二次检索本身覆盖能力
    （与整表合并后的总命中率不同）。
    """
    if not expected_apis:
        return {
            "missed_initial_count": 0,
            "recovered_count": 0,
            "new_hit_rate": None,
            "dynamic_item_count": 0,
            "rag_hit_dynamic_slice": None,
            "per_api_incremental": {},
        }

    hi = compute_rag_hit(initial_context or [], expected_apis)
    hf = compute_rag_hit(final_context or [], expected_apis)

    per_i = hi.get("per_api") or {}
    per_f = hf.get("per_api") or {}

    per_api_incremental: Dict[str, dict] = {}
    missed_initial_count = 0
    recovered_count = 0

    for api in expected_apis:
        def _hit(per: dict, key: str) -> bool:
            info = per.get(key)
            if isinstance(info, dict):
                return bool(info.get("hit", False))
            return bool(info)

        init_hit = _hit(per_i, api)
        fin_hit = _hit(per_f, api)
        if not init_hit:
            missed_initial_count += 1
        recovered = (not init_hit) and fin_hit
        if recovered:
            recovered_count += 1
        per_api_incremental[api] = {
            "initial_hit": init_hit,
            "final_hit": fin_hit,
            "recovered_by_merge": recovered,
        }

    if missed_initial_count > 0:
        new_hit_rate = round(recovered_count / missed_initial_count, 4)
    else:
        new_hit_rate = None

    dynamic_items = split_dynamic_knowledge(initial_context or [], final_context or [])
    rag_slice = compute_rag_hit(dynamic_items, expected_apis) if dynamic_items else None

    return {
        "missed_initial_count": missed_initial_count,
        "recovered_count": recovered_count,
        "new_hit_rate": new_hit_rate,
        "dynamic_item_count": len(dynamic_items),
        "rag_hit_dynamic_slice": rag_slice,
        "per_api_incremental": per_api_incremental,
    }


# ─────────────────────────────────────────────────────────────
# 执行指标
# ─────────────────────────────────────────────────────────────

def compute_pass_at_k(attempt_results: List[dict], k: int) -> bool:
    """
    Pass@k：前 k 次尝试内是否有任意一次执行成功。

    :param attempt_results: ctx.data["meta"]["attempt_results"]
    :param k: 最多考察前 k 次
    """
    for r in attempt_results[:k]:
        if r.get("success", False):
            return True
    return False


def get_success_attempt(attempt_results: List[dict]) -> Optional[int]:
    """返回第一次成功时的尝试编号（1-indexed），全部失败则返回 None。"""
    for r in attempt_results:
        if r.get("success", False):
            return r["attempt"]
    return None


# ─────────────────────────────────────────────────────────────
# 聚合统计
# ─────────────────────────────────────────────────────────────

def aggregate_metrics(task_results: List[dict]) -> dict:
    """
    按 overall 和各 complexity 等级汇总指标。

    :param task_results: pipeline 产出的 per-task 结果列表
    :return: {
        "overall": {...},
        "simple":  {...},
        "medium":  {...},
        "hard":    {...},
    }
    """
    if not task_results:
        return {}

    # 统一 complexity 命名：s1_* 任务使用 "complex"，eval_* 任务使用 "hard"，两者指同一难度
    _COMPLEXITY_MAP = {"complex": "hard"}
    for r in task_results:
        c = r.get("complexity", "unknown")
        r["complexity"] = _COMPLEXITY_MAP.get(c, c)

    complexities = sorted({r.get("complexity", "unknown") for r in task_results})

    def _agg(subset: List[dict]) -> dict:
        n = len(subset)
        if n == 0:
            return {"n": 0}

        # RAG — 区分总召回率和语义检索召回率
        rag_items       = [r["rag_hit"] for r in subset if r.get("rag_hit")]
        avg_rag         = round(sum(r["hit_rate"]      for r in rag_items) / len(rag_items), 4) if rag_items else None
        avg_unit_rag    = round(sum(r.get("unit_hit_rate", 0) for r in rag_items) / len(rag_items), 4) if rag_items else None

        # 上下文长度（token）
        init_tokens: List[int] = []
        final_tokens: List[int] = []
        for r in subset:
            ci = r.get("context_length_initial") or {}
            cf = r.get("context_length_final") or {}
            ti = ci.get("total_tokens")
            tf = cf.get("total_tokens")
            if isinstance(ti, (int, float)):
                init_tokens.append(int(ti))
            # final 缺失时（旧版 --no-exec 存 null）回退为 initial，保证 TokF(avg) 可算
            eff_final = tf if isinstance(tf, (int, float)) else ti
            if isinstance(eff_final, (int, float)):
                final_tokens.append(int(eff_final))

        avg_init_tokens = round(sum(init_tokens) / len(init_tokens), 2) if init_tokens else None
        avg_final_tokens = round(sum(final_tokens) / len(final_tokens), 2) if final_tokens else None

        # 动态 RAG：新增命中率（首轮有缺口时，合并后补上的比例）与仅动态条目的命中率
        new_hit_rates: List[float] = []
        slice_hit_rates: List[float] = []
        slice_unit_rates: List[float] = []
        for r in subset:
            inc = r.get("rag_incremental")
            if not isinstance(inc, dict):
                continue
            nh = inc.get("new_hit_rate")
            if isinstance(nh, (int, float)):
                new_hit_rates.append(float(nh))
            rs = inc.get("rag_hit_dynamic_slice")
            if isinstance(rs, dict) and rs.get("total", 0):
                hr = rs.get("hit_rate")
                ur = rs.get("unit_hit_rate")
                if isinstance(hr, (int, float)):
                    slice_hit_rates.append(float(hr))
                if isinstance(ur, (int, float)):
                    slice_unit_rates.append(float(ur))

        avg_new_hit_rate = (
            round(sum(new_hit_rates) / len(new_hit_rates), 4) if new_hit_rates else None
        )
        avg_dynamic_slice_hit_rate = (
            round(sum(slice_hit_rates) / len(slice_hit_rates), 4) if slice_hit_rates else None
        )
        avg_dynamic_slice_unit_hit_rate = (
            round(sum(slice_unit_rates) / len(slice_unit_rates), 4) if slice_unit_rates else None
        )

        # Execution
        exec_subset = [r for r in subset if r.get("execution") is not None]
        ne = len(exec_subset)
        if ne > 0:
            p1 = round(sum(1 for r in exec_subset if r["execution"].get("pass_at_1")) / ne, 4)
            p3 = round(sum(1 for r in exec_subset if r["execution"].get("pass_at_3")) / ne, 4)
        else:
            p1 = p3 = None

        return {
            "n":             n,
            "rag_hit_rate":  avg_rag,       # 总召回（unit + core 固定注入）
            "unit_hit_rate": avg_unit_rag,  # 语义检索召回（更能反映检索质量）
            "avg_new_hit_rate": avg_new_hit_rate,  # 动态合并后对「首轮缺口」的补齐率（按任务平均）
            "avg_dynamic_slice_hit_rate": avg_dynamic_slice_hit_rate,  # 仅动态新增条目的总命中率
            "avg_dynamic_slice_unit_hit_rate": avg_dynamic_slice_unit_hit_rate,  # 仅动态新增条目的语义命中率
            "avg_context_tokens_initial": avg_init_tokens,
            "avg_context_tokens_final": avg_final_tokens,
            "pass_at_1":     p1,
            "pass_at_3":     p3,
        }

    result = {"overall": _agg(task_results)}
    for c in complexities:
        result[c] = _agg([r for r in task_results if r.get("complexity") == c])
    return result


# ─────────────────────────────────────────────────────────────
# Context Length（token / chars）
# ─────────────────────────────────────────────────────────────

def _approx_token_count(text: str) -> int:
    """不依赖 tiktoken 的轻量估算（与 utils/rag_debug.py 思路一致）。"""
    parts = re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+|[^\s]", text)
    return len(parts)


def _get_cl100k_encoding() -> Any:
    """
    懒加载 cl100k_base。失败或超时时本进程内不再重试，避免反复阻塞或重复网络请求。
    环境变量：
      BENCHMARK_NO_TIKTOKEN=1  — 强制不用 tiktoken，直接走启发式
      TIKTOKEN_LOAD_TIMEOUT   — 首次加载最大等待秒数（默认 8）
    """
    global _cl100k_encoding, _cl100k_encoding_tried
    if _cl100k_encoding_tried:
        return _cl100k_encoding
    _cl100k_encoding_tried = True
    if tiktoken is None:
        return None
    if os.environ.get("BENCHMARK_NO_TIKTOKEN", "").lower() in ("1", "true", "yes"):
        return None
    try:
        timeout = float(os.environ.get("TIKTOKEN_LOAD_TIMEOUT", "8"))
    except ValueError:
        timeout = 8.0

    holder: list[Any] = [None]

    def _load() -> None:
        try:
            holder[0] = tiktoken.get_encoding("cl100k_base")
        except Exception:
            holder[0] = False

    th = threading.Thread(target=_load, daemon=True)
    th.start()
    th.join(timeout=timeout)
    if th.is_alive():
        # 仍在拉取/阻塞：避免整进程挂死
        return None
    enc = holder[0]
    if enc is None or enc is False:
        return None
    _cl100k_encoding = enc
    return _cl100k_encoding


def _count_tokens(text: str) -> int:
    text = text or ""
    if not text:
        return 0

    enc = _get_cl100k_encoding()
    if enc is not None:
        try:
            return len(enc.encode(text))
        except Exception:
            pass
    return _approx_token_count(text)


def compute_context_length(knowledge: List[dict]) -> Dict[str, Any]:
    """
    计算 RAG 上下文的总字符数与 token 估算值。

    knowledge: list[dict]，每项通常为 {"type": "...", "content": "...", "meta": {...}}。
    """
    knowledge = knowledge or []

    by_type: Dict[str, Dict[str, Any]] = {}
    total_chars = 0
    total_tokens = 0

    for item in knowledge:
        if not isinstance(item, dict):
            item_type = "raw"
            content = str(item)
        else:
            item_type = item.get("type", "unknown") or "unknown"
            content = item.get("content", "") or ""

        chars = len(content)
        toks = _count_tokens(content)

        total_chars += chars
        total_tokens += toks

        bucket = by_type.setdefault(item_type, {"count": 0, "chars": 0, "tokens": 0})
        bucket["count"] += 1
        bucket["chars"] += chars
        bucket["tokens"] += toks

    return {
        "total_chars": total_chars,
        "total_tokens": total_tokens,
        "by_type": by_type,
    }

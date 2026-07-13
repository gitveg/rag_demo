"""
benchmark/rag_adapter.py
========================
格式适配层：将 GenesisAgent._retrieve() 返回的结构化 dict
转换为 compute_rag_hit() 所需的 list[dict] 格式。

rag_demo 的 _retrieve() 返回：
  {
    "ku_title", "ku_desc", "ku_code",
    "api_docs": str,           # 拼接后的 API 文档
    "key_apis": list[str],
    "ref_code_fallback": str,
    "ref_title_fallback": str,
  }

compute_rag_hit() 期望：
  list[dict]，每项 {"type": str, "content": str, "meta": dict}

适配器负责解析 api_docs 字符串，还原为独立的知识条目。
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from agent import GenesisAgent


# ─────────────────────────────────────────────────────────────
# api_docs 解析用的正则
# ─────────────────────────────────────────────────────────────

# 匹配 "--- CORE API: {api_id} ---" 或 "--- API Reference: {api_id} ---" 或 "--- API Search Result ---"
_RE_API_BLOCK = re.compile(
    r"^--- (?:CORE API:\s*(?P<core_id>\S+)|API Reference:\s*(?P<ref_id>\S+)|API Search Result) ---",
    re.MULTILINE,
)


def _parse_api_docs(api_docs: str) -> List[dict]:
    """
    将 _retrieve() 拼接的 api_docs 字符串拆分为独立的 API 条目。

    api_docs 格式示例：
      --- CORE API: genesis.Scene.add_entity ---
      API 文档内容...

      --- API Reference: genesis.morphs.Sphere ---
      API 文档内容...

      --- API Search Result ---
      API 文档内容...

    返回 list[dict]，每项：
      {"type": "api", "content": "--- (CORE )API: id ---\\n...", "meta": {"api_id": ..., ...}}
    """
    if not api_docs or not api_docs.strip():
        return []

    # 找到所有分隔符的位置
    matches = list(_RE_API_BLOCK.finditer(api_docs))
    if not matches:
        # 无分隔符时整个字符串作为一条
        return [{"type": "api", "content": api_docs, "meta": {}}]

    items: List[dict] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(api_docs)
        block = api_docs[start:end].strip()

        core_id = m.group("core_id")
        ref_id = m.group("ref_id")

        if core_id:
            items.append({
                "type": "api",
                "content": f"--- CORE API: {core_id} ---\n{block}",
                "meta": {"api_id": core_id, "is_core": True},
            })
        elif ref_id:
            items.append({
                "type": "api",
                "content": f"--- API Reference: {ref_id} ---\n{block}",
                "meta": {"api_id": ref_id, "is_core": False},
            })
        else:
            # --- API Search Result ---
            # 尝试从 content 中提取 api_id（如果文档内含 api_id 字段）
            api_id = _extract_api_id_from_doc(block)
            items.append({
                "type": "api",
                "content": f"--- API: {block[:50]}...\n{block}",
                "meta": {"api_id": api_id} if api_id else {},
            })

    return items


def _extract_api_id_from_doc(doc: str) -> str:
    """
    尝试从 API 文档文本中提取 api_id。
    常见格式：
      - "api_id: genesis.Scene.add_entity"
      - 文档第一行含 genesis.xxx.yyy
    """
    # 匹配 "api_id: xxx" 或 "API: xxx" 格式
    m = re.search(r'(?:api_id|API)\s*:\s*(genesis\.\w+(?:\.\w+)*)', doc, re.IGNORECASE)
    if m:
        return m.group(1)
    # 回退：匹配第一个 genesis.xxx.yyy 模式
    m = re.search(r'(genesis\.\w+\.\w+)', doc)
    if m:
        return m.group(1)
    return ""


def retrieve_to_knowledge_list(retrieval: dict) -> List[dict]:
    """
    将 GenesisAgent._retrieve() 返回的结构化 dict 转为
    compute_rag_hit() 所需的 list[dict] 格式。

    :param retrieval: _retrieve() 的返回值
    :return: 适配后的知识条目列表
    """
    items: List[dict] = []

    # --- 1. Knowledge Unit ---
    ku_code = retrieval.get("ku_code", "")
    if ku_code and ku_code != "No reference available.":
        # 从 _retrieve() 逻辑中，key_apis 来自知识单元的 meta.key_apis 或 meta.all_apis
        key_apis = retrieval.get("key_apis", [])
        key_apis_str = ",".join(key_apis)
        items.append({
            "type": "unit",
            "content": ku_code,
            "meta": {
                "title": retrieval.get("ku_title", "N/A"),
                "desc": retrieval.get("ku_desc", ""),
                "all_apis": key_apis_str,  # 用于 compute_rag_hit 的精确匹配
                "key_apis": key_apis_str,
            },
        })

    # --- 2. API Docs (Core + Reference + Search) ---
    api_docs = retrieval.get("api_docs", "")
    items.extend(_parse_api_docs(api_docs))

    # --- 3. Code Fallback ---
    ref_code = retrieval.get("ref_code_fallback", "")
    if ref_code:
        items.append({
            "type": "code",
            "content": ref_code,
            "meta": {"title": retrieval.get("ref_title_fallback", "N/A")},
        })

    return items


def rag_fast_search(agent: "GenesisAgent", query: str) -> List[dict]:
    """
    快速模式：只做 rewrite → classify → retrieve，
    不生成代码、不执行。返回适配后的知识列表。

    用于 benchmark --no-exec 模式。

    :param agent: 已初始化的 GenesisAgent
    :param query: 原始用户查询
    :return: 适配后的知识条目列表，可直接传给 compute_rag_hit()
    """
    # Step 1: Query Rewriting
    rewrite_result = agent.rewriter.rewrite(query, mode=agent.rewrite_mode)
    search_query = rewrite_result["search_query"]

    # Step 2: Intent Classification
    intent_tag = agent._classify_intent(query)

    # Step 3: Retrieval
    retrieval = agent._retrieve(search_query, intent_tag)

    # Step 4: Format adaptation
    return retrieve_to_knowledge_list(retrieval)

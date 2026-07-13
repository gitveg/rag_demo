"""
loop_a/metadata_gen.py — 回路 A 的 LLM 元数据生成。

为执行成功的代码生成 title/description/tags，
复用 indexer_code.py 的 SYSTEM_PROMPT 和 ALLOWED_TAGS。
"""

from __future__ import annotations

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAG_DEMO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, RAG_DEMO_ROOT)


def init_llm():
    """初始化 DeepSeek LLM 客户端。"""
    try:
        from openai import OpenAI
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return None
        return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    except ImportError:
        return None


def generate_metadata(code: str, query: str, source_id: str = "") -> tuple:
    """
    调用 LLM 为成功代码生成 title/description/tags。

    复用 indexer_code.py 的 SYSTEM_PROMPT 和 ALLOWED_TAGS。

    Returns:
        (title, desc, tags)
    """
    llm = init_llm()
    if llm is None:
        title = query[:50] + ("..." if len(query) > 50 else "")
        return title, f"Runtime success: {query}", ["runtime_feedback"]

    from indexers.indexer_code import SYSTEM_PROMPT, ALLOWED_TAGS

    user_prompt = f"""Analyze the following Genesis physics simulation script and generate metadata.

Script:
{code[:2000]}... (truncated)

User Task: {query}

Return JSON:
{{
    "title": "Concise title (e.g., 'Rigid Ball Drop Simulation')",
    "description": "One sentence summary",
    "tags": {json.dumps(ALLOWED_TAGS)}
}}"""

    try:
        resp = llm.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        text = (resp.choices[0].message.content or "").strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return (
            result.get("title", source_id or query[:50]),
            result.get("description", ""),
            result.get("tags", ["runtime_feedback"]),
        )
    except Exception:
        return source_id or query[:50], f"Runtime success: {query}", ["runtime_feedback"]

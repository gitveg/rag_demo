"""
查询重写模块：在 RAG 检索前对用户 query 进行变换，缩小自然语言与代码知识库的语义鸿沟。

支持两种模式（可叠加）：
  - translate : 将中文 query 翻译为英文技术描述（如果已是英文则原样返回）
  - hyde      : HyDE（Hypothetical Document Embeddings）—— 让 LLM 生成一段伪代码骨架，
                用伪代码的 embedding 去检索 API/代码知识库，召回率显著优于原始自然语言。

适配 rag_demo 的 LLMClient（messages 列表接口）。
"""

import os
import sys
import re

# 确保能 import rag_demo 根目录的模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_utils import LLMClient
import dotenv

dotenv.load_dotenv()

_TRANSLATE_SYSTEM = (
    "You are a technical translator. "
    "If the input contains Chinese, translate it into concise English technical description "
    "suitable for a physics simulation search query. "
    "If the input is already in English, return it unchanged. "
    "Output ONLY the translated text, no explanation."
)

_HYDE_SYSTEM = (
    "You are a Genesis physics engine expert. "
    "Given a simulation task description, write a SHORT Python pseudocode skeleton "
    "that sketches which Genesis objects and methods you would use. "
    "Do NOT explain. Output ONLY the code block, no markdown fences."
)

_HYDE_USER_TMPL = (
    "Task: {query}\n\n"
    "Write a concise pseudocode skeleton using Genesis API (e.g. gs.Scene, scene.add_entity, "
    "gs.morphs.Sphere, gs.materials.Rigid, scene.build, scene.step, etc.). "
    "Keep it under 20 lines."
)

_CN_PATTERN = re.compile(r"[一-鿿]")


class QueryRewriter:
    """查询重写器。内部懒加载 LLMClient，首次调用时才初始化。"""

    def __init__(self, provider="openai", api_key=None, base_url=None, model=None):
        self._llm = None
        self._provider = provider
        self._api_key = api_key
        self._base_url = base_url
        self._model = model

    def _get_llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient(
                provider=self._provider,
                api_key=self._api_key or os.getenv("DEEPSEEK_API_KEY"),
                base_url=self._base_url or os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com"),
                model=self._model or "deepseek-chat",
            )
        return self._llm

    def _chat(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        """统一调用 rag_demo 的 LLMClient（messages 列表接口）"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        result = self._get_llm().chat(messages, temperature=temperature)
        return result if result else ""

    # ------------------------------------------------------------------
    def translate(self, query: str) -> str:
        """如果 query 含中文，翻译为英文技术描述；否则原样返回。"""
        if not _CN_PATTERN.search(query):
            return query
        try:
            result = self._chat(_TRANSLATE_SYSTEM, query, temperature=0.1)
            return result if result and not result.startswith("Error:") else query
        except Exception as e:
            print(f"[QueryRewriter] translate failed, fallback to original. Error: {e}")
            return query

    # ------------------------------------------------------------------
    def hyde(self, query: str) -> str:
        """HyDE：生成 Genesis 伪代码骨架，与知识库处于同一语义空间。"""
        try:
            result = self._chat(_HYDE_SYSTEM, _HYDE_USER_TMPL.format(query=query), temperature=0.2)
            return result if result and not result.startswith("Error:") else query
        except Exception as e:
            print(f"[QueryRewriter] hyde failed, fallback to original. Error: {e}")
            return query

    # ------------------------------------------------------------------
    def rewrite(self, query: str, mode: str = "none") -> dict:
        """
        统一重写入口。

        :param query: 原始用户 query
        :param mode:  "none" / "translate" / "hyde"
        :return: {
            "original": str,
            "translated": str,     # (translate/hyde 模式)
            "hyde_code": str,      # (hyde 模式)
            "search_query": str,   # 实际用于检索的 query
        }
        """
        result = {"original": query, "search_query": query}

        if mode == "none":
            return result

        translated = self.translate(query)
        result["translated"] = translated

        if mode == "translate":
            result["search_query"] = translated
            return result

        hyde_code = self.hyde(translated)
        result["hyde_code"] = hyde_code
        result["search_query"] = hyde_code

        return result

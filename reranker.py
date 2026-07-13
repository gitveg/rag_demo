"""
Reranker：基于 DashScope gte-rerank-v2 的交叉编码器重排序模块。

使用方式：
    reranker = Reranker()
    reranked = reranker.rerank(query="...", items=[...], top_n=3)

items 格式与 RAGInterface.search() 返回值相同：
    [{"type": str, "content": str, "meta": dict}, ...]

重排后每个 item 的 meta 中会注入 "rerank_score" 字段，便于 debug/audit。
调用失败时静默 fallback 到原始排序，不影响主流程。

依赖：dashscope（已作为 embedding 依赖安装）
环境变量：DASHSCOPE_API_KEY、DASHSCOPE_NATIVE_API_URL、RERANK_MODEL_NAME
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional


class Reranker:
    """
    封装 DashScope TextReRank API，提供 list[dict] 粒度的重排序接口。
    内部懒加载 dashscope 模块，避免 import 时触发网络连接。
    """

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or os.getenv("RERANK_MODEL_NAME", "gte-rerank-v2")
        self._api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self._base_url = os.getenv(
            "DASHSCOPE_NATIVE_API_URL",
            "https://dashscope.aliyuncs.com/api/v1",
        ).rstrip("/")

    def rerank(
        self,
        query: str,
        items: List[dict],
        top_n: Optional[int] = None,
        content_max_chars: int = 1000,
        min_score: float = 0.0,
    ) -> List[dict]:
        """
        对 items 按照与 query 的语义相关度重新排序。

        :param query:             用户原始查询（中英文均可，gte-rerank-v2 支持 50+ 语言）
        :param items:             RAGInterface.search() 返回的知识列表
        :param top_n:             保留前 N 条；None 则保留全部（仅重排不截断）
        :param content_max_chars: 每条 document 传给 rerank API 的最大字符数（防止超 token 限制）
        :param min_score:         过滤掉 relevance_score < min_score 的条目
        :return:                  重排后的 items 列表（每项 meta 增加 "rerank_score"）
        """
        if not items:
            return items

        effective_top_n = top_n if top_n is not None else len(items)
        # unit 类型优先使用精简的 rerank_text（~300 chars），避免长 rich_content 被 cross-encoder 截断
        documents = []
        for x in items:
            if x.get("type") == "unit":
                rt = x.get("meta", {}).get("rerank_text", "")
                if rt:
                    documents.append(rt[:max(content_max_chars, 600)])
                else:
                    documents.append(x["content"][:max(content_max_chars, 2000)])
            else:
                documents.append(x["content"][:content_max_chars])

        try:
            import dashscope  # 懒加载，与项目其余模块风格一致
            dashscope.base_http_api_url = self._base_url

            resp = dashscope.TextReRank.call(
                model=self.model,
                query=query,
                documents=documents,
                top_n=effective_top_n,
                return_documents=False,
                api_key=self._api_key,
            )

            if resp.status_code != 200:
                raise RuntimeError(
                    f"Rerank API 返回异常: status={resp.status_code} message={resp.message}"
                )

            # 按 relevance_score 降序（API 已排好序，但显式排序更稳健）
            ranked = sorted(
                resp.output.results,
                key=lambda r: r.relevance_score,
                reverse=True,
            )

            result: List[dict] = []
            for r in ranked:
                if min_score > 0 and float(r.relevance_score) < min_score:
                    continue
                original_item = items[r.index]
                item = dict(original_item)
                item["meta"] = dict(original_item["meta"])
                item["meta"]["rerank_score"] = round(float(r.relevance_score), 4)
                result.append(item)

            return result

        except Exception as exc:
            print(f"[Reranker] WARNING: rerank 调用失败，使用原始排序。原因: {exc}")
            return items

    def rerank_by_groups(
        self,
        query: str,
        items: List[dict],
        group_top_n: Dict[str, Optional[int]],
        content_max_chars: int = 1000,
        min_score: float = 0.0,
    ) -> List[dict]:
        """
        按 item type 分组 rerank，每组独立 top_n，避免长文档和短文档竞争。

        :param query:         用户查询
        :param items:         知识列表
        :param group_top_n:   各类型的 top_n 配置，如 {"unit": 3, "default": 8}
                              未指定的类型回退到 "default"；default 缺省则不截断
        :param content_max_chars: 传给 rerank API 的最大字符数
        :param min_score:     过滤低分条目
        :return:              重排后的 items 列表
        """
        if not items:
            return items
        groups: Dict[str, List[dict]] = {}
        for item in items:
            groups.setdefault(item.get("type", "unknown"), []).append(item)
        result: List[dict] = []
        for gtype, group_items in groups.items():
            top_n = group_top_n.get(gtype, group_top_n.get("default", None))
            reranked = self.rerank(
                query=query, items=group_items, top_n=top_n,
                content_max_chars=content_max_chars, min_score=min_score,
            )
            result.extend(reranked)
        return result

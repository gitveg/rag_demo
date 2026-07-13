"""
hybrid_search.py — 混合检索模块。

提供：
  - SymbolMatcher：API 符号提取 + 候选重排（当前推荐）
  - HybridTokenizer：中文/英文/API 名称混合分词
  - HybridSearch：BM25 索引构建、搜索、RRF 融合（备选，KB 规模扩大后启用）
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

import numpy as np


# ==================== 领域词汇表 ====================
# 这些 token 对 BM25 匹配至关重要，需要被 jieba 保留为完整词
GENESIS_DOMAIN_TERMS = [
    # 类/命名空间
    "Scene", "Entity", "Camera", "Light", "Emitter", "Sensor",
    "Viewer", "Simulator", "Solver", "Coupler",
    # 材质/物理
    "Rigid", "Soft", "MPM", "SPH", "FEM", "PBD", "SFP", "Avatar",
    # 形态
    "Sphere", "Box", "Plane", "Cylinder", "Mesh", "Terrain",
    "Capsule", "Cone", "Torus", "Polygon",
    # Morph
    "MJCF", "URDF", "Morph",
    # 子模块
    "Morphs", "Materials", "Surfaces", "Textures", "Renderers",
    "Sensors", "Options", "Textures",
    # 渲染
    "Rasterizer", "RayTracer", "Rasterize", "Rasterization",
    # 机器人
    "Robot", "Joint", "Link", "Motor", "Actuator",
    # 常见 API 组件
    "ViewerOptions", "SimOptions", "RigidOptions", "MPMOptions",
    "SPHOptions", "FEMOptions", "VisOptions", "ProfilingOptions",
    "ToolOptions", "CouplerOptions",
    # 操作
    "add_entity", "add_camera", "add_light", "add_emitter", "add_sensor",
    "add_force_field", "build", "step", "reset", "destroy",
    # Genesis 本身
    "genesis", "Genesis", "gs",
    # 常见缩写
    "APIs", "API", "GPU", "CPU", "DDP", "RGB", "FPS",
]


# ==================== 停用词 ====================
STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "must",
    "and", "or", "but", "if", "then", "else", "when", "while", "for",
    "in", "on", "at", "to", "of", "with", "by", "from", "as", "into",
    "this", "that", "these", "those", "it", "its", "not", "no",
    "import", "def", "class", "return", "self", "none", "true", "false",
    "print", "range", "len", "list", "dict", "set", "tuple",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "they",
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有",
    "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些", "什么",
    "如何", "怎么", "可以", "创建", "实现", "使用", "生成", "添加",
})


# ==================== 分词器 ====================

# CamelCase 拆分
_CAMEL_RE = re.compile(r"([A-Z][a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\b)|[a-z]+|\d+)")
# 点分标识符
_DOT_ID_RE = re.compile(r"(?:gs|genesis)\.([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)")
# 下划线标识符
_UNDERSCORE_ID_RE = re.compile(r"[a-z][a-z0-9]*(?:_[a-z][a-z0-9]*)+")
# 英文单词（纯字母序列）
_WORD_RE = re.compile(r"[A-Za-z]{2,}")


class HybridTokenizer:
    """混合分词器：处理中文 + 英文 + Genesis API 名称。"""

    def __init__(self):
        import jieba

        self._jieba = jieba
        # 将领域词汇加入 jieba 词库，确保不被错误切分
        for term in GENESIS_DOMAIN_TERMS:
            self._jieba.add_word(term)
        # 静默模式，抑制 jieba 的初始化日志
        self._jieba.setLogLevel(20)

    def tokenize(self, text: str) -> List[str]:
        """
        对混合文本分词，返回 token 列表。

        处理流程：
        1. 提取 gs.xxx.yyy / genesis.xxx.yyy → 拆为独立 token
        2. CamelCase 拆分
        3. jieba 中文分词
        4. 过滤停用词和短 token
        """
        if not text:
            return []

        tokens = []

        # Step 1: 提取并拆分 API 点分标识符
        api_tokens = set()
        text_for_jieba = text
        for m in _DOT_ID_RE.finditer(text):
            full = m.group(0)
            # gs.xxx → genesis.xxx
            if full.startswith("gs."):
                full = "genesis." + full[3:]
            parts = full.split(".")
            for p in parts:
                p_lower = p.lower()
                if len(p_lower) >= 2 and p_lower not in STOP_WORDS:
                    api_tokens.add(p_lower)
                # CamelCase 拆分
                for sub in _CAMEL_RE.findall(p):
                    sub_lower = sub.lower()
                    if len(sub_lower) >= 2 and sub_lower not in STOP_WORDS:
                        api_tokens.add(sub_lower)
        tokens.extend(api_tokens)

        # Step 2: jieba 分词（处理中文 + 残余英文）
        # 去掉 API 路径部分避免重复，但保留普通文本
        jieba_text = _DOT_ID_RE.sub(" ", text)
        for word in self._jieba.cut(jieba_text):
            word = word.strip()
            if not word or len(word) < 2:
                continue
            # 纯英文：lowercase + CamelCase 拆分
            if word.isascii() and word.isalpha():
                word_lower = word.lower()
                if word_lower in STOP_WORDS:
                    continue
                tokens.append(word_lower)
                for sub in _CAMEL_RE.findall(word):
                    sub_lower = sub.lower()
                    if sub_lower != word_lower and len(sub_lower) >= 2 and sub_lower not in STOP_WORDS:
                        tokens.append(sub_lower)
            elif any("一" <= c <= "鿿" for c in word):
                # 中文词
                if word not in STOP_WORDS:
                    tokens.append(word)
            # 混合 token（如 "3D", "MPM"）
            elif len(word) >= 2:
                tokens.append(word.lower())

        return tokens


# ==================== BM25 搜索 ====================

class HybridSearch:
    """
    BM25 + Dense 混合检索。

    在 ChromaDB dense 检索之上叠加 BM25 sparse 检索，
    通过 RRF (Reciprocal Rank Fusion) 融合两者排序。
    """

    def __init__(self):
        self._bm25_indexes: Dict[str, "BM25Okapi"] = {}
        self._corpus_ids: Dict[str, List[str]] = {}
        self._corpus_docs: Dict[str, List[str]] = {}
        self._corpus_metas: Dict[str, List[dict]] = {}
        self._tokenized_corpus: Dict[str, List[List[str]]] = {}
        self._tokenizer = HybridTokenizer()

    # ---- 索引构建 ----

    def build_index(self, name: str, ids: List[str],
                    documents: List[str], metadatas: List[dict]):
        """
        从 ChromaDB collection 数据构建 BM25 索引。

        :param name: 索引名称（如 "knowledge_units", "apis"）
        :param ids: 文档 ID 列表
        :param documents: 文档文本列表
        :param metadatas: 元数据列表
        """
        from rank_bm25 import BM25Okapi

        # 分词
        tokenized = [self._tokenizer.tokenize(doc) for doc in documents]

        self._corpus_ids[name] = ids
        self._corpus_docs[name] = documents
        self._corpus_metas[name] = metadatas
        self._tokenized_corpus[name] = tokenized
        self._bm25_indexes[name] = BM25Okapi(tokenized)

        print(f"  [HybridSearch] BM25 索引已构建: {name} ({len(ids)} 条文档)")

    def has_index(self, name: str) -> bool:
        return name in self._bm25_indexes

    # ---- BM25 搜索 ----

    def search(self, name: str, query: str, top_k: int = 20,
               tag_filter: str = None) -> List[dict]:
        """
        BM25 搜索。

        :param name: 索引名称
        :param query: 查询文本
        :param top_k: 返回前 K 个结果
        :param tag_filter: 可选 tag 过滤（后过滤）
        :return: [{"id", "score", "metadata", "document"}, ...]
        """
        if not self.has_index(name):
            return []

        query_tokens = self._tokenizer.tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25_indexes[name].get_scores(query_tokens)

        # 按分数降序排列，取 oversample 候选（留余量给 tag 过滤）
        oversample = min(top_k * 3, len(scores))
        top_indices = np.argsort(scores)[::-1][:oversample]

        results = []
        for idx in top_indices:
            if scores[idx] <= 0:
                continue
            meta = self._corpus_metas[name][idx]

            # Tag 后过滤
            if tag_filter:
                tags = meta.get("tags", "")
                if tag_filter not in tags:
                    continue

            results.append({
                "id": self._corpus_ids[name][idx],
                "score": float(scores[idx]),
                "metadata": meta,
                "document": self._corpus_docs[name][idx],
            })
            if len(results) >= top_k:
                break

        return results

    # ---- RRF 融合 ----

    @staticmethod
    def reciprocal_rank_fusion(
        dense_results: List[dict],
        sparse_results: List[dict],
        k: int = 60,
        top_n: Optional[int] = None,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
    ) -> List[dict]:
        """
        加权 RRF (Reciprocal Rank Fusion) 融合稠密和稀疏检索结果。

        score(d) = w_dense * 1/(k + rank_dense(d)) + w_sparse * 1/(k + rank_sparse(d))

        :param dense_results: 稠密检索结果 [{"id", "document", "metadata", "distance"}, ...]
        :param sparse_results: 稀疏检索结果 [{"id", "score", "metadata", "document"}, ...]
        :param k: RRF 参数（默认 60，经验值）
        :param top_n: 保留前 N 个结果；None 保留全部
        :param dense_weight: 稠密路径权重（默认 0.7）
        :param sparse_weight: 稀疏路径权重（默认 0.3）
        :return: 融合后的结果列表，按 RRF score 降序
        """
        # 累积加权 RRF 分数
        rrf_scores: Dict[str, float] = {}
        # 保存文档数据（用第一次出现的为准）
        doc_data: Dict[str, dict] = {}

        # Dense 路径
        for rank, item in enumerate(dense_results, 1):
            doc_id = item["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + dense_weight / (k + rank)
            if doc_id not in doc_data:
                doc_data[doc_id] = {
                    "id": doc_id,
                    "document": item.get("document", ""),
                    "metadata": item.get("metadata", {}),
                    "distance": item.get("distance"),
                    "bm25_score": None,
                }

        # Sparse 路径
        for rank, item in enumerate(sparse_results, 1):
            doc_id = item["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + sparse_weight / (k + rank)
            if doc_id not in doc_data:
                doc_data[doc_id] = {
                    "id": doc_id,
                    "document": item.get("document", ""),
                    "metadata": item.get("metadata", {}),
                    "distance": None,
                    "bm25_score": item.get("score"),
                }
            elif doc_data[doc_id]["bm25_score"] is None:
                doc_data[doc_id]["bm25_score"] = item.get("score")

        # 按 RRF score 降序
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        results = []
        for doc_id in sorted_ids:
            item = doc_data[doc_id]
            item["rrf_score"] = rrf_scores[doc_id]
            results.append(item)

        if top_n is not None:
            results = results[:top_n]

        return results

    # ---- 格式转换 ----

    @staticmethod
    def to_chroma_format(fused_results: List[dict]) -> dict:
        """
        将融合结果转换为 ChromaDB query() 返回格式。

        返回: {"ids": [[...]], "documents": [[...]], "metadatas": [[...]], "distances": [[...]]}
        """
        ids = [r["id"] for r in fused_results]
        documents = [r["document"] for r in fused_results]
        metadatas = [r["metadata"] for r in fused_results]
        # distance 用 rrf_score 的负数（越小越好，与 ChromaDB cosine distance 一致）
        distances = [-r["rrf_score"] for r in fused_results]

        return {
            "ids": [ids],
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances],
        }

    @staticmethod
    def chroma_to_dense_items(chroma_result: dict) -> List[dict]:
        """
        将 ChromaDB query() 结果转换为 dense_items 列表。

        ChromaDB 格式: {"ids": [[id1, ...]], "documents": [[doc1, ...]],
                         "metadatas": [[meta1, ...]], "distances": [[dist1, ...]]}
        """
        if not chroma_result or not chroma_result.get("ids") or not chroma_result["ids"][0]:
            return []

        items = []
        for i in range(len(chroma_result["ids"][0])):
            items.append({
                "id": chroma_result["ids"][0][i],
                "document": chroma_result["documents"][0][i] if chroma_result.get("documents") else "",
                "metadata": chroma_result["metadatas"][0][i] if chroma_result.get("metadatas") else {},
                "distance": chroma_result["distances"][0][i] if chroma_result.get("distances") else None,
            })
        return items


# ==================== API Symbol Matcher ====================

# 匹配 gs.xxx.yyy 或 genesis.xxx.yyy 形式的 API 调用
_API_SYMBOL_RE = re.compile(
    r'(?:gs|genesis)\.([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)'
)


class SymbolMatcher:
    """
    API 符号提取 + 候选重排。

    从查询文本（HyDE 伪代码）中提取 Genesis API 符号，
    与候选知识单元的 all_apis 元数据做精确集合匹配，
    给匹配度高的候选加分，实现零噪声的符号级重排。
    """

    def __init__(self, known_apis: set):
        """
        :param known_apis: 标准化后的已知 API ID 集合（从 genesis_api_index.json 加载）
        """
        self._known_apis = known_apis

    @property
    def known_apis(self) -> set:
        return self._known_apis

    def extract_symbols(self, text: str) -> List[str]:
        """
        从文本中提取 Genesis API 符号并标准化。

        处理流程：
        1. 正则匹配 gs.xxx.yyy / genesis.xxx.yyy 模式
        2. gs 前缀补全为 genesis
        3. 通过 resolve_api_to_known() 映射到标准 API ID
        4. 去重并过滤未知 API

        :param text: 查询文本（通常是 HyDE 伪代码）
        :return: 标准化后的 API ID 列表
        """
        from api_id_normalize import resolve_api_to_known

        raw_symbols = []
        for m in _API_SYMBOL_RE.finditer(text):
            path = m.group(1)
            # 补全前缀：gs.morphs.Sphere -> genesis.morphs.Sphere
            full = "genesis." + path
            raw_symbols.append(full)

        # 标准化到已知 API ID
        resolved = set()
        for sym in raw_symbols:
            canonical = resolve_api_to_known(sym, self._known_apis)
            if canonical:
                resolved.add(canonical)

        return sorted(resolved)

    def boost_rank(
        self,
        dense_results: dict,
        query_symbols: List[str],
        top_n: int,
        alpha: float = 0.3,
    ) -> dict:
        """
        对 Dense 检索结果做符号加分重排。

        score = (1-alpha) * dense_norm + alpha * overlap_ratio

        :param dense_results: ChromaDB query() 格式结果（含多个候选）
        :param query_symbols: 从查询提取的标准化 API 符号列表
        :param top_n: 最终返回数量
        :param alpha: 符号匹配权重（默认 0.3，Dense 权重 0.7）
        :return: ChromaDB 格式结果（重排后的 top_n）
        """
        if not dense_results or not dense_results.get("ids") or not dense_results["ids"][0]:
            return dense_results

        n_candidates = len(dense_results["ids"][0])

        # 如果没有查询符号，直接返回原始 Dense 结果（截取 top_n）
        if not query_symbols:
            return _truncate_chroma(dense_results, top_n)

        query_set = set(query_symbols)

        # 计算每个候选的融合分数
        scored = []
        distances = dense_results.get("distances", [[]])[0]
        for i in range(n_candidates):
            doc_id = dense_results["ids"][0][i]
            doc_text = dense_results["documents"][0][i] if dense_results.get("documents") else ""
            meta = dense_results["metadatas"][0][i] if dense_results.get("metadatas") else {}
            dist = distances[i] if distances else 0.5

            # Dense 归一化: cosine distance [0, 2] → similarity [0, 1]
            dense_sim = max(0.0, 1.0 - dist / 2.0)

            # 符号重叠率
            all_apis_str = meta.get("all_apis", "") or meta.get("key_apis", "")
            unit_apis = set(a.strip() for a in all_apis_str.split(",") if a.strip())
            overlap = len(query_set & unit_apis)
            overlap_ratio = overlap / max(len(query_set), 1)

            # 加权融合
            final_score = (1 - alpha) * dense_sim + alpha * overlap_ratio

            scored.append({
                "id": doc_id,
                "document": doc_text,
                "metadata": meta,
                "distance": dist,
                "final_score": final_score,
                "overlap": overlap,
            })

        # 按 final_score 降序排列
        scored.sort(key=lambda x: x["final_score"], reverse=True)
        scored = scored[:top_n]

        # 转回 ChromaDB 格式
        ids = [r["id"] for r in scored]
        documents = [r["document"] for r in scored]
        metadatas = [r["metadata"] for r in scored]
        # distance 用 final_score 的负数（与 ChromaDB 一致：越小越好）
        out_distances = [-r["final_score"] for r in scored]

        return {
            "ids": [ids],
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [out_distances],
        }


def _truncate_chroma(results: dict, top_n: int) -> dict:
    """截取 ChromaDB 格式结果的前 top_n 条。"""
    if not results or not results.get("ids") or not results["ids"][0]:
        return results
    n = min(top_n, len(results["ids"][0]))
    return {
        "ids": [results["ids"][0][:n]],
        "documents": [results["documents"][0][:n]] if results.get("documents") else [[]],
        "metadatas": [results["metadatas"][0][:n]] if results.get("metadatas") else [[]],
        "distances": [results["distances"][0][:n]] if results.get("distances") else [[]],
    }

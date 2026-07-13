import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from openai import OpenAI
import json
import os
from tqdm import tqdm
import dotenv

dotenv.load_dotenv()

# ================= 配置区域 =================
# 所有路径基于 rag_engine.py 所在目录（rag_demo/）解析，避免 CWD 依赖
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库持久化路径
DB_PATH = os.path.join(_BASE_DIR, "genesis_chroma_db")

# 数据源文件
API_FILE     = os.path.join(_BASE_DIR, "knowledge_base", "genesis_api_index.json")
CODE_FILE    = os.path.join(_BASE_DIR, "knowledge_base", "genesis_code_index.json")
SNIPPET_FILE = os.path.join(_BASE_DIR, "knowledge_base", "genesis_code_snippets.json")
ERROR_FILE   = os.path.join(_BASE_DIR, "knowledge_base", "genesis_error_memory.json")
UNIT_FILE    = os.path.join(_BASE_DIR, "knowledge_base", "genesis_knowledge_units.json")

# API Key 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "你的_DASHSCOPE_API_KEY")
DASHSCOPE_API_URL = os.getenv(
    "DASHSCOPE_API_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
).rstrip("/")
DASHSCOPE_EMBEDDING_MODEL = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4")

# 人为排除的 Core API：灌库时强制不标为 core，避免重跑 indexer_api 后又被标回 core
CORE_API_BLACKLIST = [
    "genesis.options.SFOptions",
    "genesis.options.ProfilingOptions",
]

# ================= 自定义 Embedding Function =================
class DashScopeEmbeddingFunction(EmbeddingFunction):
    """
    自定义 Chroma 嵌入函数，用于调用阿里百炼 (DashScope) 
    """
    def __init__(self, api_key: str, base_url: str = "", model_name: str = ""):

        self.openai_client = OpenAI(
            api_key=api_key,
            base_url=(base_url or DASHSCOPE_API_URL).rstrip("/"),
        )
        self.model_name = model_name or DASHSCOPE_EMBEDDING_MODEL
        self.dimensions = 1024

    def __call__(self, input: Documents) -> Embeddings:
        # 移除换行符
        clean_input = [text.replace("\n", " ") for text in input]

        try:
            response = self.openai_client.embeddings.create(
                model=self.model_name,
                input=clean_input,
                dimensions=self.dimensions, 
                encoding_format="float"
            )
            # 排序提取向量
            data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in data]
            
        except Exception as e:
            print(f"[FAIL] Embedding API 调用失败: {e}")
            raise e

# ================= RAG 引擎主类 =================
class GenesisRAG:
    def __init__(self, reset_db=False, use_hybrid=True):
        """
        初始化 RAG 引擎

        :param reset_db: 是否重置 ChromaDB
        :param use_hybrid: 是否启用 BM25 + Dense 混合检索
        """
        self.chroma_client = chromadb.PersistentClient(path=DB_PATH)

        # 初始化 Embedding 函数
        self.embedding_fn = DashScopeEmbeddingFunction(
            api_key=DASHSCOPE_API_KEY,
            base_url=DASHSCOPE_API_URL,
            model_name=DASHSCOPE_EMBEDDING_MODEL,
        )

        # 清除旧数据逻辑
        if reset_db:
            collections_to_reset = [
                "genesis_apis",
                "genesis_examples",
                "genesis_snippets",
                "genesis_errors",
                "genesis_knowledge_units",
            ]
            for col_name in collections_to_reset:
                try:
                    self.chroma_client.delete_collection(col_name)
                    print(f"[DEL]️  已清除旧集合: {col_name}")
                except Exception:
                    pass

        # 获取或创建集合 (API 和 Code)
        self.api_collection = self.chroma_client.get_or_create_collection(
            name="genesis_apis",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        self.code_collection = self.chroma_client.get_or_create_collection(
            name="genesis_examples",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        # 新增：获取或创建集合 (Snippets 和 Errors)
        self.snippet_collection = self.chroma_client.get_or_create_collection(
            name="genesis_snippets",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        self.error_collection = self.chroma_client.get_or_create_collection(
            name="genesis_errors",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        self.unit_collection = self.chroma_client.get_or_create_collection(
            name="genesis_knowledge_units",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        # 混合检索：Symbol Boost（API 符号匹配 + Dense 重排）
        self._use_hybrid = use_hybrid
        self._symbol_matcher = None
        if self._use_hybrid:
            self._init_symbol_matcher()

        # 距离阈值：余弦距离超过此值的结果将被丢弃（与 phys_agent 对齐）
        self.DISTANCE_THRESHOLD = 0.5

    def _filter_by_distance(self, results, threshold=None):
        """
        过滤 ChromaDB 查询结果，丢弃余弦距离超过阈值的结果。
        与 phys_agent/core/rag_interface.py 的 _filter_by_distance() 逻辑一致。

        :param results: ChromaDB query() 返回的 dict（含 ids/documents/metadatas/distances）
        :param threshold: 距离阈值（默认使用 self.DISTANCE_THRESHOLD）
        :return: 过滤后的同结构 dict
        """
        if threshold is None:
            threshold = self.DISTANCE_THRESHOLD

        if "distances" not in results or not results["distances"] or not results["distances"][0]:
            return results

        distances = results["distances"][0]
        keep = [i for i, d in enumerate(distances) if d <= threshold]

        if not keep:
            # 全部被过滤，返回空结果（保持 ChromaDB 嵌套列表格式）
            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

        filtered = {}
        for key in ("ids", "documents", "metadatas", "distances"):
            if key in results and results[key]:
                filtered[key] = [[results[key][0][i] for i in keep]]
            else:
                filtered[key] = [[]]
        return filtered

    def _init_symbol_matcher(self):
        """初始化 SymbolMatcher：从 API 索引加载 known_apis。"""
        from hybrid_search import SymbolMatcher

        api_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), API_FILE)
        if not os.path.exists(api_file):
            print("  [SymbolBoost] WARNING: genesis_api_index.json not found, hybrid disabled")
            return

        with open(api_file, "r", encoding="utf-8") as f:
            api_data = json.load(f)
        known_apis = set(a["api_id"] for a in api_data if a.get("api_id"))
        self._symbol_matcher = SymbolMatcher(known_apis)
        print(f"  [SymbolBoost] 已加载 {len(known_apis)} 个已知 API")

    # ---------------- API 入库 ----------------
    def ingest_apis(self):
        """导入 API 数据"""
        if not os.path.exists(API_FILE):
            print(f"[FAIL] 找不到文件: {API_FILE}")
            return

        with open(API_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"📥 正在导入 {len(data)} 个 API 条目...")
        
        BATCH_SIZE = 10
        for i in tqdm(range(0, len(data), BATCH_SIZE), desc="Ingesting APIs"):
            batch_data = data[i : i + BATCH_SIZE]
            
            ids = []
            docs = []
            metas = []

            for item in batch_data:
                ids.append(item['api_id'])
                # 文档结构：API + Summary + Signature + Parameters（仅含有效 desc）+ Constraints
                doc_text = f"API: {item['api_id']}\nSummary: {item.get('summary', '')}\n"
                if item.get('signature'):
                    doc_text += f"Signature: {item['signature']}\n"
                if 'parameters' in item:
                    # 排除占位描述（Auto-Detect、Needs LLM expansion.）以缩短上下文
                    def _valid_desc(desc):
                        if not desc:
                            return False
                        return "Auto-Detect" not in desc and "Needs LLM expansion." not in desc
                    p_desc = ", ".join([
                        f"{p['name']}: {p.get('desc', '')}"
                        for p in item['parameters']
                        if _valid_desc(p.get('desc', ''))
                    ])
                    if p_desc:
                        doc_text += f"Parameters: {p_desc}\n"
                if 'constraints' in item:
                    doc_text += f"Constraints: {', '.join(item['constraints'])}"
                
                docs.append(doc_text)

                domain_tags_list = item.get("domain_tags", []) or []
                if item["api_id"] in CORE_API_BLACKLIST:
                    domain_tags_list = [t for t in domain_tags_list if t != "core"]
                metas.append({
                    "type": item['type'],
                    "domain_tags": ",".join(domain_tags_list),
                    "is_core": ("core" in domain_tags_list),
                    "signature": item.get('signature', ''),
                })
            
            if ids:
                self.api_collection.add(ids=ids, documents=docs, metadatas=metas)

    # ---------------- 完整代码入库 ----------------
    def ingest_code(self):
        """导入完整代码范例"""
        if not os.path.exists(CODE_FILE):
            print(f"[FAIL] 找不到文件: {CODE_FILE}")
            return

        with open(CODE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"📥 正在导入 {len(data)} 个代码范例...")
        
        BATCH_SIZE = 10
        for i in tqdm(range(0, len(data), BATCH_SIZE), desc="Ingesting Code"):
            batch_data = data[i : i + BATCH_SIZE]
            ids = []
            docs = []
            metas = []

            for item in batch_data:
                ids.append(item['id'])
                meta = item.get('metadata', {})
                doc_text = f"Title: {meta.get('title', '')}\nDescription: {meta.get('desc', '')}\nTags: {', '.join(meta.get('tags', []))}"
                docs.append(doc_text)
                metas.append({
                    "title": meta.get('title', ''),
                    "tags": ",".join(meta.get('tags', [])),
                    "key_apis": ",".join(meta.get('key_apis', [])),
                    "code_snippet": item['code'][:1000]
                })
            
            if ids:
                self.code_collection.add(ids=ids, documents=docs, metadatas=metas)

    # ---------------- 新增：代码片段入库 ----------------
    def ingest_snippets(self):
        """导入代码片段"""
        if not os.path.exists(SNIPPET_FILE):
            print(f"[FAIL] 找不到文件: {SNIPPET_FILE} (Code Snippets)")
            return

        with open(SNIPPET_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"📥 正在导入 {len(data)} 个代码片段...")
        # 百炼 embedding 单次最多 10 条，与 ingest_apis/ingest_code 一致
        BATCH_SIZE = 10
        for i in tqdm(range(0, len(data), BATCH_SIZE), desc="Ingesting Snippets"):
            batch_data = data[i : i + BATCH_SIZE]
            ids = []
            docs = []
            metas = []

            for item in batch_data:
                # 确保有 ID
                if 'id' not in item: continue
                ids.append(item['id'])
                
                # Document: 任务描述 + 代码本身 (增加语义匹配度)
                doc_text = f"Task: {item.get('task', 'Unknown task')}\nCode: {item.get('code', '')}"
                docs.append(doc_text)
                
                # Metadata
                metas.append({
                    "task": item.get('task', ''),
                    "code": item.get('code', ''), # 将代码存入 metadata 方便直接取用
                    "key_apis": ",".join(item.get('key_apis', [])),
                    "tags": ",".join(item.get('tags', []))
                })
            
            if ids:
                self.snippet_collection.add(ids=ids, documents=docs, metadatas=metas)

    # ---------------- 新增：错误记忆入库 ----------------
    def ingest_errors(self):
        """导入错误记忆"""
        if not os.path.exists(ERROR_FILE):
            print(f"[FAIL] 找不到文件: {ERROR_FILE} (Error Memory)")
            return

        with open(ERROR_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"📥 正在导入 {len(data)} 条错误记忆...")
        # 百炼 embedding 单次最多 10 条
        BATCH_SIZE = 10
        for i in tqdm(range(0, len(data), BATCH_SIZE), desc="Ingesting Errors"):
            batch_data = data[i : i + BATCH_SIZE]
            ids = []
            docs = []
            metas = []

            for item in batch_data:
                if 'id' not in item: continue
                ids.append(item['id'])
                
                # Document: 包含上下文、错误模式和纠正方案
                doc_text = (f"Context: {item.get('query_context', '')}\n"
                            f"Bad Pattern: {item.get('bad_pattern', '')}\n"
                            f"Correction: {item.get('correction', '')}\n"
                            f"Explanation: {item.get('explanation', '')}")
                docs.append(doc_text)
                
                metas.append({
                    "bad_pattern": item.get('bad_pattern', ''),
                    "correction": item.get('correction', ''),
                    "explanation": item.get('explanation', ''),
                    "tags": ",".join(item.get('tags', []))
                })
            
            if ids:
                self.error_collection.add(ids=ids, documents=docs, metadatas=metas)

    # ---------------- 知识单元入库 ----------------
    def ingest_knowledge_units(self):
        """导入知识单元（代码文件 + 内嵌 API 文档摘要的聚合体，为 HyDE 检索优化）。
        需先运行 indexer_knowledge_units.py 生成 genesis_knowledge_units.json。
        """
        if not os.path.exists(UNIT_FILE):
            print(f"[FAIL] 找不到文件: {UNIT_FILE}，请先运行 indexer_knowledge_units.py")
            return

        with open(UNIT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"📥 正在导入 {len(data)} 个知识单元...")
        BATCH_SIZE = 10
        for i in tqdm(range(0, len(data), BATCH_SIZE), desc="Ingesting Knowledge Units"):
            batch_data = data[i: i + BATCH_SIZE]
            ids, docs, metas = [], [], []
            for u in batch_data:
                ids.append(u["unit_id"])
                docs.append(u["embedding_text"])   # 代码风格文本，用于向量化（HyDE 对齐）
                api_summaries = "\n".join(
                    f"{d['api_id']}: {d.get('summary', '')[:150]}"
                    + (f"\n  Signature: {d['signature']}" if d.get("signature") else "")
                    for d in u.get("api_docs", [])
                )[:2000]
                metas.append({
                    "title":         u.get("title", ""),
                    "desc":          u.get("desc", "")[:300],
                    "tags":          ",".join(u.get("tags", [])),
                    "all_apis":      ",".join(u.get("all_apis", []) or u.get("key_apis", [])),
                    "key_apis":      ",".join(u.get("key_apis", [])),
                    "api_summaries": api_summaries,
                    "code_preview":  u.get("code", "")[:600],
                })
            if ids:
                self.unit_collection.add(ids=ids, documents=docs, metadatas=metas)

    # ---------------- 混合检索 ----------------
    def _symbol_boost_search(self, collection, query, n_results,
                              tag_filter=None, oversample_factor=3, alpha=0.3):
        """
        Dense + API Symbol Boost 混合检索。

        1. Dense 检索获取 top-K 候选（oversample）
        2. 从查询文本提取 API 符号
        3. 按符号重叠率对候选加分重排
        4. 返回 top_n

        :param collection: ChromaDB collection 对象
        :param query: 查询文本（HyDE 伪代码）
        :param n_results: 最终返回数量
        :param tag_filter: 可选 tag 过滤
        :param oversample_factor: Dense oversample 倍数
        :param alpha: 符号匹配权重
        :return: ChromaDB 格式结果
        """
        k_dense = min(n_results * oversample_factor, collection.count())

        # Dense 检索（oversample）
        where_clause = None
        if tag_filter:
            where_clause = {"tags": {"$contains": tag_filter}}
        try:
            dense_raw = collection.query(
                query_texts=[query], n_results=k_dense, where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            dense_raw = collection.query(query_texts=[query], n_results=k_dense,
                                         include=["documents", "metadatas", "distances"])

        # 距离阈值过滤：丢弃弱匹配候选后再做 symbol boost 重排
        dense_raw = self._filter_by_distance(dense_raw)
        if not dense_raw["ids"] or not dense_raw["ids"][0]:
            return dense_raw  # 全部被过滤，返回空

        # 提取查询 API 符号
        query_symbols = self._symbol_matcher.extract_symbols(query)

        # Symbol Boost 重排
        return self._symbol_matcher.boost_rank(
            dense_raw, query_symbols, top_n=n_results, alpha=alpha
        )

    # ---------------- 检索方法 ----------------
    def search_code(self, query, n_results=3, tag_filter=None):
        """检索完整代码范例"""
        where_clause = None
        if tag_filter:
            where_clause = {"tags": {"$contains": tag_filter}}

        try:
            res = self.code_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            res = self.code_collection.query(query_texts=[query], n_results=n_results,
                                             include=["documents", "metadatas", "distances"])
        return self._filter_by_distance(res)

    def search_snippet(self, query, n_results=3, tag_filter=None):
        """检索代码片段"""
        where_clause = None
        if tag_filter:
            where_clause = {"tags": {"$contains": tag_filter}}

        try:
            res = self.snippet_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            res = self.snippet_collection.query(query_texts=[query], n_results=n_results,
                                                include=["documents", "metadatas", "distances"])
        return self._filter_by_distance(res)

    def search_error(self, query, n_results=3, tag_filter=None):
        """检索错误记忆"""
        where_clause = None
        if tag_filter:
            where_clause = {"tags": {"$contains": tag_filter}}

        try:
            res = self.error_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            res = self.error_collection.query(query_texts=[query], n_results=n_results,
                                              include=["documents", "metadatas", "distances"])
        return self._filter_by_distance(res)

    def search_knowledge_units(self, query, n_results=3, tag_filter=None):
        """检索知识单元（HyDE 优化后的聚合知识体）"""
        if self._use_hybrid and self._symbol_matcher:
            return self._symbol_boost_search(
                self.unit_collection, query, n_results,
                tag_filter=tag_filter,
            )

        where_clause = None
        if tag_filter:
            where_clause = {"tags": {"$contains": tag_filter}}

        try:
            res = self.unit_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            res = self.unit_collection.query(query_texts=[query], n_results=n_results,
                                             include=["documents", "metadatas", "distances"])
        return self._filter_by_distance(res)

    def search_api(self, query, n_results=10):
        res = self.api_collection.query(
            query_texts=[query], n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        return self._filter_by_distance(res)

    def get_core_api_docs(self, limit=30):
        try:
            res = self.api_collection.get(where={"is_core": True}, limit=limit)
        except Exception:
            res = self.api_collection.get(where={"domain_tags": {"$contains": "core"}}, limit=limit)

        ids = res.get("ids") or []
        docs = res.get("documents") or []
        return list(zip(ids, docs))

    # ================= 统一 search 入口（与 phys_agent 对齐）=================
    def search(
        self,
        query: str,
        n_api: int = 6,
        n_code: int = 1,
        n_snippet: int = 3,
        n_error: int = 0,
        tag_filter: str = None,
        include_core_api: bool = True,
        core_api_limit: int = 40,
        rewrite_mode: str = "hyde",
        n_units: int = 5,
        hyde_route: str = "unit",
        use_hybrid: bool = None,
        distance_threshold: float = None,
        rerank: bool = False,
        rerank_top_n: int = None,
        rerank_oversample: float = 2.0,
    ):
        """
        统一检索入口，签名与 phys_agent/core/rag_interface.py 完全对齐。

        路由逻辑：
          - rewrite_mode == "hyde" and hyde_route == "unit"  →  知识单元路径
          - 其他所有情况（none / translate / hyde+fourway）  →  四路检索路径

        :param use_hybrid: 是否启用 Symbol Boost 混合检索。None 表示使用 __init__ 默认值。
        :param distance_threshold: 余弦距离过滤阈值。None 表示使用 __init__ 默认值（0.5）。
        :return: list[dict]，每项 {"type": "api"|"unit"|"code"|"snippet"|"error",
                                    "content": str, "meta": dict}
        """
        if hyde_route not in ("unit", "fourway"):
            hyde_route = "unit"

        # ---------- 查询重写 ----------
        if rewrite_mode != "none":
            from query_rewriter import QueryRewriter
            rewriter = QueryRewriter()
            rewrite_result = rewriter.rewrite(query, mode=rewrite_mode)
            effective_query = rewrite_result["search_query"]
            if rewrite_result.get("translated") and rewrite_result["translated"] != query:
                print(f"  [QueryRewriter] translated : {rewrite_result['translated']}")
            if rewrite_result.get("hyde_code"):
                lines = rewrite_result["hyde_code"].splitlines()
                preview = " | ".join(lines[:3]) + (" ..." if len(lines) > 3 else "")
                print(f"  [QueryRewriter] hyde_code  : {preview}")
            print(f"  [QueryRewriter] search_query: {effective_query[:120]}")
        else:
            rewrite_result = {"original": query, "search_query": query}
            effective_query = query

        self._last_rewrite_result = rewrite_result

        # rerank 超采样
        _os = rerank_oversample if rerank else 1.0
        _n_units   = max(1, int(n_units * _os))
        _n_api     = max(1, int(n_api * _os))
        _n_code    = max(1, int(n_code * _os))
        _n_snippet = max(1, int(n_snippet * _os))

        # ---- 临时覆盖基础设施参数（save/restore）----
        _saved_hybrid = self._use_hybrid
        _saved_threshold = self.DISTANCE_THRESHOLD
        if use_hybrid is not None:
            self._use_hybrid = use_hybrid
        if distance_threshold is not None:
            self.DISTANCE_THRESHOLD = distance_threshold
        try:
            return self._search_body(
                effective_query, n_api, n_code, n_snippet, n_error,
                tag_filter, include_core_api, core_api_limit,
                rewrite_mode, n_units, hyde_route,
                rerank, rerank_top_n, _os, rewrite_result,
                _n_units, _n_api, _n_code, _n_snippet,
            )
        finally:
            self._use_hybrid = _saved_hybrid
            self.DISTANCE_THRESHOLD = _saved_threshold

    # ================= Rerank 辅助方法 =================
    def _apply_rerank(self, query: str, items: list, rerank_top_n: int = None) -> list:
        """
        对检索结果调用 Reranker 做交叉编码器重排序。
        调用失败时静默 fallback 到原始排序，不影响主流程。
        """
        try:
            from reranker import Reranker
            reranker = Reranker()
            reranked = reranker.rerank(query=query, items=items, top_n=rerank_top_n)
            print(f"  [Rerank] 重排完成: {len(items)} → {len(reranked)} 条"
                  + (f" (top_n={rerank_top_n})" if rerank_top_n else ""))
            return reranked
        except Exception as exc:
            print(f"  [Rerank] WARNING: rerank 调用失败，使用原始排序。原因: {exc}")
            return items

    # ================= search 实现体（内部）=================
    def _search_body(
        self, effective_query, n_api, n_code, n_snippet, n_error,
        tag_filter, include_core_api, core_api_limit,
        rewrite_mode, n_units, hyde_route,
        rerank, rerank_top_n, _os, rewrite_result,
        _n_units, _n_api, _n_code, _n_snippet,
    ):
        # 去重基础设施
        out = []
        seen = set()
        seen_api_ids = set()

        def add(t: str, content: str, meta: dict, api_id_for_dedup: str = None):
            key = (t, content[:200])
            if key in seen:
                return
            if t == "api" and api_id_for_dedup is not None and api_id_for_dedup in seen_api_ids:
                return
            seen.add(key)
            if t == "api" and api_id_for_dedup:
                seen_api_ids.add(api_id_for_dedup)
            out.append({"type": t, "content": content, "meta": meta or {}})

        # ============================================================
        # 路由：hyde + unit → 知识单元检索
        # ============================================================
        if rewrite_mode == "hyde" and hyde_route == "unit":
            # --- 1) 知识单元检索 ---
            unit_res = self.search_knowledge_units(
                effective_query, n_results=_n_units, tag_filter=tag_filter
            )
            unit_ids_list   = unit_res.get("ids", [[]])[0] or []
            unit_metas_list = unit_res.get("metadatas", [[]])[0] or []

            # 收集单元已覆盖的 api_ids
            covered_api_ids = set()
            for meta in unit_metas_list:
                if isinstance(meta, dict):
                    api_field = meta.get("all_apis", "") or meta.get("key_apis", "")
                    for k in api_field.split(","):
                        k = k.strip()
                        if k:
                            covered_api_ids.add(k)
            seen_api_ids.update(covered_api_ids)

            # 格式化单元内容
            for j, meta in enumerate(unit_metas_list):
                if not isinstance(meta, dict):
                    continue
                uid           = unit_ids_list[j] if j < len(unit_ids_list) else ""
                title         = meta.get("title", "")
                desc          = meta.get("desc", "")
                tags_str      = meta.get("tags", "")
                all_apis_str  = meta.get("all_apis", "")
                key_apis_str  = meta.get("key_apis", "")
                api_summaries = meta.get("api_summaries", "")
                code_preview  = meta.get("code_preview", "")
                rich_content = (
                    f"=== Knowledge Unit: {title} ===\n"
                    f"Domain: {tags_str}  |  All APIs: {all_apis_str}  |  Key APIs: {key_apis_str}\n"
                    f"Description: {desc}\n\n"
                    f"--- API Reference ---\n{api_summaries}\n\n"
                    f"--- Code Example ---\n{code_preview}"
                )
                add("unit", rich_content, {
                    "unit_id": uid,
                    "all_apis": all_apis_str,
                    "key_apis": key_apis_str,
                    "title": title,
                })

            # --- 1.5) 代码范例 fallback（知识单元全部被距离阈值过滤时兜底）---
            if not unit_ids_list and n_code > 0:
                code_res = self.search_code(
                    effective_query, n_results=n_code, tag_filter=tag_filter
                )
                code_ids   = code_res.get("ids", [[]])[0] or []
                code_metas = code_res.get("metadatas", [[]])[0] or []
                for j, mid in enumerate(code_metas):
                    title   = (mid.get("title") or "") if isinstance(mid, dict) else ""
                    snippet = (mid.get("code_snippet") or "") if isinstance(mid, dict) else ""
                    cid = code_ids[j] if j < len(code_ids) else ""
                    if snippet:
                        add("code", f"Title: {title}\n{snippet}",
                            {"id": cid, "title": title})

            # --- 2) Core API 注入（去重）---
            if include_core_api:
                for api_id, doc in self.get_core_api_docs(limit=core_api_limit):
                    if api_id not in covered_api_ids:
                        add("api", f"--- CORE API: {api_id} ---\n{doc}",
                            {"api_id": api_id, "is_core": True}, api_id_for_dedup=api_id)

            # --- 3) API 语义检索补充 ---
            if n_api > 0 and len(out) < n_api + core_api_limit:
                api_res = self.search_api(effective_query, n_results=n_api)
                api_ids0  = api_res.get("ids", [[]])[0] or []
                api_docs0 = api_res.get("documents", [[]])[0] or []
                for j, doc in enumerate(api_docs0):
                    aid = api_ids0[j] if j < len(api_ids0) else ""
                    add("api", f"--- API: {aid} ---\n{doc}",
                        {"api_id": aid}, api_id_for_dedup=aid)

            # --- 4) 错误记忆 ---
            if n_error > 0:
                err_res = self.search_error(effective_query, n_results=n_error)
                metas0 = err_res.get("metadatas", [[]])[0] or []
                for mid in metas0:
                    if not isinstance(mid, dict):
                        continue
                    bad  = mid.get("bad_pattern", "")
                    corr = mid.get("correction", "")
                    exp  = mid.get("explanation", "")
                    add("error", f"Bad: {bad} → Correction: {corr}. {exp}", mid)

            # --- Rerank（知识单元路径）---
            if rerank and out:
                out = self._apply_rerank(effective_query, out, rerank_top_n)

            return out

        # ============================================================
        # 路由：四路检索（none / translate / hyde+fourway）
        # ============================================================

        # 1) Core API（无条件全量注入）
        if include_core_api:
            for api_id, doc in self.get_core_api_docs(limit=core_api_limit):
                add("api", f"--- CORE API: {api_id} ---\n{doc}",
                    {"api_id": api_id, "is_core": True}, api_id_for_dedup=api_id)

        # 2) API 语义检索
        if n_api and n_api > 0:
            api_res = self.search_api(effective_query, n_results=_n_api)
            ids0  = api_res.get("ids", [[]])[0] or []
            docs0 = api_res.get("documents", [[]])[0] or []
            for j, doc in enumerate(docs0):
                aid = ids0[j] if j < len(ids0) else ""
                add("api", f"--- API: {aid} ---\n{doc}",
                    {"api_id": aid}, api_id_for_dedup=aid)

        # 3) 完整代码范例
        if n_code and n_code > 0:
            code_res = self.search_code(effective_query, n_results=_n_code, tag_filter=tag_filter)
            ids0   = code_res.get("ids", [[]])[0] or []
            metas0 = code_res.get("metadatas", [[]])[0] or []
            for j, mid in enumerate(metas0):
                title   = (mid.get("title") or "") if isinstance(mid, dict) else ""
                snippet = (mid.get("code_snippet") or "") if isinstance(mid, dict) else ""
                cid = ids0[j] if j < len(ids0) else ""
                add("code", f"Title: {title}\n{snippet}", {"id": cid, "title": title})

        # 4) 代码片段
        if n_snippet and n_snippet > 0:
            snip_res = self.search_snippet(effective_query, n_results=_n_snippet, tag_filter=tag_filter)
            ids0   = snip_res.get("ids", [[]])[0] or []
            metas0 = snip_res.get("metadatas", [[]])[0] or []
            for j, mid in enumerate(metas0):
                task = (mid.get("task") or "") if isinstance(mid, dict) else ""
                code = (mid.get("code") or "") if isinstance(mid, dict) else ""
                sid  = ids0[j] if j < len(ids0) else ""
                add("snippet", f"Task: {task}\n{code}", {"id": sid, "task": task})

        # 5) 错误记忆
        if n_error > 0:
            err_res = self.search_error(effective_query, n_results=n_error)
            metas0 = err_res.get("metadatas", [[]])[0] or []
            for mid in metas0:
                if not isinstance(mid, dict):
                    continue
                bad  = mid.get("bad_pattern", "")
                corr = mid.get("correction", "")
                exp  = mid.get("explanation", "")
                add("error", f"Bad: {bad} → Correction: {corr}. {exp}", mid)

        # --- Rerank（四路检索路径）---
        if rerank and out:
            out = self._apply_rerank(effective_query, out, rerank_top_n)

        return out

if __name__ == "__main__":
    if "你的" in DASHSCOPE_API_KEY and not os.getenv("DASHSCOPE_API_KEY"):
        print("[FAIL] 警告: 请务必先在代码开头填入你的 DASHSCOPE_API_KEY")
    else:
        # 重置并灌入数据
        rag = GenesisRAG(reset_db=True)
        rag.ingest_apis()
        rag.ingest_code()
        rag.ingest_snippets()
        rag.ingest_errors()
        rag.ingest_knowledge_units()

        # 重新灌库后重建 Symbol Matcher
        rag._init_symbol_matcher()

        print("\n🔎 测试完整代码检索: 'Soft body simulation'")
        res = rag.search_code("Soft body simulation")
        print(f"Results: {len(res['ids'][0])}")

        print("\n🔎 测试 Snippet 检索: 'Create ground plane'")
        res = rag.search_snippet("Create ground plane")
        if res['ids'][0]:
            print(f"Snippet Found: {res['metadatas'][0][0]['code']}")

        print("\n🔎 测试 Error 检索: 'scene.add(box)'")
        res = rag.search_error("I used scene.add(box) and it failed")
        if res['ids'][0]:
            print(f"Error Rule Found: {res['metadatas'][0][0]['explanation']}")

        print("\n🔎 测试 Symbol Boost (知识单元): 'gs.morphs.MJCF robot arm'")
        res = rag.search_knowledge_units("gs.morphs.MJCF robot arm", n_results=3)
        for i, uid in enumerate(res['ids'][0]):
            print(f"  [{i+1}] {uid} — {res['metadatas'][0][i].get('title','')}")

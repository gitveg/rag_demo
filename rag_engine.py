import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from openai import OpenAI
import json
import os
from tqdm import tqdm
import dotenv

dotenv.load_dotenv()

# ================= 配置区域 =================
# 数据库持久化路径
DB_PATH = "./genesis_chroma_db"

# 数据源文件
API_FILE = "genesis_knowledge_base_final.json"
CODE_FILE = "genesis_code_index.json" 
# 新增：代码片段与错误记忆文件
SNIPPET_FILE = "genesis_code_snippets.json"
ERROR_FILE = "genesis_error_memory.json"
UNIT_FILE = "genesis_knowledge_units.json"

# API Key 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "你的_DASHSCOPE_API_KEY")

# 人为排除的 Core API：灌库时强制不标为 core，避免重跑 indexer/enricher 后又被标回 core
CORE_API_BLACKLIST = [
    "genesis.options.SFOptions",
    "genesis.options.ProfilingOptions",
]

# ================= 自定义 Embedding Function =================
class DashScopeEmbeddingFunction(EmbeddingFunction):
    """
    自定义 Chroma 嵌入函数，用于调用阿里百炼 (DashScope) 
    """
    def __init__(self, api_key: str):

        self.openai_client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.model_name = "text-embedding-v4"
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
            print(f"❌ Embedding API 调用失败: {e}")
            raise e

# ================= RAG 引擎主类 =================
class GenesisRAG:
    def __init__(self, reset_db=False):
        """
        初始化 RAG 引擎
        """
        self.chroma_client = chromadb.PersistentClient(path=DB_PATH)
        
        # 初始化 Embedding 函数
        self.embedding_fn = DashScopeEmbeddingFunction(api_key=DASHSCOPE_API_KEY)

        # 清除旧数据逻辑
        if reset_db:
            collections_to_reset = ["genesis_apis", "genesis_examples", "genesis_snippets", "genesis_errors"]
            for col_name in collections_to_reset:
                try:
                    self.chroma_client.delete_collection(col_name)
                    print(f"🗑️  已清除旧集合: {col_name}")
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

    # ---------------- API 入库 ----------------
    def ingest_apis(self):
        """导入 API 数据"""
        if not os.path.exists(API_FILE):
            print(f"❌ 找不到文件: {API_FILE}")
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
            print(f"❌ 找不到文件: {CODE_FILE}")
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
            print(f"❌ 找不到文件: {SNIPPET_FILE} (Code Snippets)")
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
            print(f"❌ 找不到文件: {ERROR_FILE} (Error Memory)")
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
            print(f"❌ 找不到文件: {UNIT_FILE}，请先运行 indexer_knowledge_units.py")
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
                    "key_apis":      ",".join(u.get("key_apis", [])),
                    "api_summaries": api_summaries,
                    "code_preview":  u.get("code", "")[:600],
                })
            if ids:
                self.unit_collection.add(ids=ids, documents=docs, metadatas=metas)

    # ---------------- 检索方法 ----------------
    def search_code(self, query, n_results=3, tag_filter=None):
        """检索完整代码范例"""
        where_clause = None
        if tag_filter:
            where_clause = {"tags": {"$contains": tag_filter}}

        try:
            return self.code_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
        except Exception:
            return self.code_collection.query(query_texts=[query], n_results=n_results)

    def search_snippet(self, query, n_results=3, tag_filter=None):
        """检索代码片段"""
        where_clause = None
        if tag_filter:
            where_clause = {"tags": {"$contains": tag_filter}}

        try:
            return self.snippet_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
        except Exception:
            return self.snippet_collection.query(query_texts=[query], n_results=n_results)

    def search_error(self, query, n_results=3, tag_filter=None):
        """检索错误记忆"""
        where_clause = None
        if tag_filter:
            where_clause = {"tags": {"$contains": tag_filter}}

        try:
            return self.error_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
        except Exception:
            # 错误记忆如果不带 filter 搜不到，可能意味着没有通用错误，返回空或者尝试裸搜
            return self.error_collection.query(query_texts=[query], n_results=n_results)

    def search_api(self, query, n_results=10):
        return self.api_collection.query(query_texts=[query], n_results=n_results)

    def get_core_api_docs(self, limit=30):
        try:
            res = self.api_collection.get(where={"is_core": True}, limit=limit)
        except Exception:
            res = self.api_collection.get(where={"domain_tags": {"$contains": "core"}}, limit=limit)

        ids = res.get("ids") or []
        docs = res.get("documents") or []
        return list(zip(ids, docs))

if __name__ == "__main__":
    if "你的" in DASHSCOPE_API_KEY and not os.getenv("DASHSCOPE_API_KEY"):
        print("❌ 警告: 请务必先在代码开头填入你的 DASHSCOPE_API_KEY")
    else:
        # 重置并灌入数据
        rag = GenesisRAG(reset_db=True)
        rag.ingest_apis()
        rag.ingest_code()
        rag.ingest_snippets()
        rag.ingest_errors()
        rag.ingest_knowledge_units()  # 新增：知识单元（HyDE 检索用）
        
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
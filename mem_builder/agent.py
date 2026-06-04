"""
Genesis RAG Agent — 基于知识单元检索的代码生成 Agent。

Pipeline:
  1. Query Rewriting（translate + HyDE 伪代码）
  2. 知识单元检索（primary）+ API 文档补充
  3. LLM 生成完整可运行代码

可被 build_api_constraint.py 直接 import 调用，也可通过 CLI 独立运行。
"""

import argparse
import json
import os
import re
import sys
import time
import dotenv

# 确保能 import rag_demo 根目录的模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_utils import LLMClient
from rag_engine import GenesisRAG
from mem_builder.query_rewriter import QueryRewriter

dotenv.load_dotenv()

# ================= 1. API CONFIGURATION =================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com")

# ================= 2. DOMAIN CONSTANTS =================
VALID_TAGS = [
    "rigid_body", "soft_body", "fluid_mpm", "fluid_sph", "articulated_robot",
    "scene_creation", "interaction", "rendering", "camera_control",
]

# ================= 3. PROMPT TEMPLATES =================
PROMPT_CLASSIFY_INTENT = """
You are a Query Classifier for a Physics Engine.
Classify the User Query into EXACTLY ONE of the following categories:
{tags_json}

Rules:
1. If query involves deformation/elasticity/cloth/flesh, choose 'soft_body'.
2. If query involves water/liquid/sand, choose 'fluid_mpm'.
3. If query involves robots/joints, choose 'articulated_robot'.
4. If query is just basic shapes falling/colliding, choose 'rigid_body'.
5. Return ONLY the tag string. No markdown, no punctuation.

User Query: "{query}"
"""

PROMPT_GEN_SYSTEM = """
You are an expert coding assistant for the Genesis Physics Engine.
Generate a complete, runnable Python script based on the User Query.

Priority of truth (highest to lowest):
1) Reference Code (from knowledge unit): copy its overall structure and API usage patterns.
2) API Docs: use as a hint for names and available attributes; it may be incomplete.
3) Your own guesses: NOT allowed.

Hard rules (must follow):
- Output MUST be runnable Python (no pseudo-code).
- Always initialize with `gs.init()` and create a `gs.Scene(...)`.
- DO NOT invent APIs, attributes, enum values, or parameters.
  If an option/argument/attribute is not shown in the Reference Code AND not present in API Docs, DO NOT use it.
- Prefer defaults: if the user did not explicitly ask for advanced solver/options tuning, do not set those fields at all.
- Keep calls minimal: pass only the minimum necessary arguments.
- If there is a conflict between Reference Code and API Docs, follow the Reference Code and simplify.

Common hallucination traps to avoid:
- Enums: never use enum members that are not explicitly listed in API Docs / reference.
- Modules vs callables: some names are modules (e.g., `gs.materials.FEM`) and are not callable; use concrete classes/functions.

Self-check before finalizing:
- Scan your code for any dotted attribute like `gs.xxx.yyy`. If you cannot point to it in the Reference Code or API Docs, remove it.
- If you added optional config/options, try deleting them unless the user requested them.
"""

PROMPT_GEN_USER = """
User Query: {query}

--- Reference Knowledge Unit ({intent}) ---
Title: {ku_title}
Description: {ku_desc}
Reference Code:
{ku_code}

--- API Documentation (Reference) ---
{api_docs}

Task:
- Write the full Python code for the user query.
- Follow the Reference Code's structure and style as closely as possible.
- Use API Docs only as a reference for parameter details; if something is missing/unclear, prefer the Reference Code and keep it minimal.
- Avoid advanced options unless the user asked for them; defaults are preferred.

Output format:
- Output ONLY the Python code (no markdown fences, no explanations).
"""

# ================= 4. AGENT LOGIC =================
class GenesisAgent:
    def __init__(
        self,
        use_knowledge_units=True,
        use_api=True,
        use_code=False,
        use_snippets=False,
        use_errors=False,
        rewrite_mode="hyde",
    ):
        """
        :param use_knowledge_units: 主检索——知识单元（推荐开启）
        :param use_api: 是否补充检索 API 文档
        :param use_code: 是否检索完整代码范例（fallback）
        :param use_snippets: 是否检索代码片段
        :param use_errors: 是否检索错误记忆
        :param rewrite_mode: "none" / "translate" / "hyde"
        """
        self.use_knowledge_units = use_knowledge_units
        self.use_api = use_api
        self.use_code = use_code
        self.use_snippets = use_snippets
        self.use_errors = use_errors
        self.rewrite_mode = rewrite_mode

        # 1. LLM
        self.llm = LLMClient(
            provider="openai",
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_API_URL,
            model="deepseek-reasoner",
        )

        # 2. RAG
        self.rag = GenesisRAG(reset_db=False)

        # 3. Query Rewriter
        self.rewriter = QueryRewriter()

    # ------------------------------------------------------------------
    #  Intent Classification
    # ------------------------------------------------------------------
    def _classify_intent(self, query):
        prompt = PROMPT_CLASSIFY_INTENT.format(
            tags_json=json.dumps(VALID_TAGS),
            query=query,
        )
        try:
            response = self.llm.chat([{"role": "user", "content": prompt}], temperature=0.01)
            if not response:
                return None
            tag = response.strip().replace("'", "").replace('"', "")
            return tag if tag in VALID_TAGS else None
        except Exception:
            return None

    # ------------------------------------------------------------------
    #  Code helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_code(response: str) -> str:
        """从 LLM 返回中提取 Python 代码"""
        pattern = r"```(?:python)?\s*(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.replace("```python", "").replace("```", "").strip()

    def save_generated_code(self, code_content, output_dir="code"):
        """保存生成的代码到本地文件"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"agent_code_{timestamp}.py"
        file_path = os.path.join(output_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code_content)
        print(f"  [Agent] Code saved to: {file_path}")
        return file_path

    # ------------------------------------------------------------------
    #  Retrieval
    # ------------------------------------------------------------------
    def _retrieve(self, query, intent_tag):
        """
        核心检索逻辑。返回 dict:
          {
            "ku_title", "ku_desc", "ku_code",      # 知识单元
            "api_docs": str,                          # API 文档拼接
            "key_apis": list,                         # 引用到的 API ID 列表
            "ref_code_fallback": str,                 # 完整代码范例（fallback）
            "ref_title_fallback": str,
          }
        """
        result = {
            "ku_title": "N/A",
            "ku_desc": "",
            "ku_code": "No reference available.",
            "api_docs": "",
            "key_apis": [],
            "ref_code_fallback": "",
            "ref_title_fallback": "",
        }

        # --- Primary: Knowledge Units ---
        if self.use_knowledge_units:
            print("  [Agent] Searching knowledge units...")
            ku_results = self.rag.search_knowledge_units(
                query, n_results=1, tag_filter=intent_tag
            )
            if ku_results["ids"] and ku_results["ids"][0]:
                meta = ku_results["metadatas"][0][0]
                result["ku_title"] = meta.get("title", "N/A")
                result["ku_desc"] = meta.get("desc", "")
                result["ku_code"] = meta.get("code_preview", "")
                key_apis_str = meta.get("key_apis", "") or meta.get("all_apis", "")
                result["key_apis"] = [a.strip() for a in key_apis_str.split(",") if a.strip()]
                print(f"  [Agent] Knowledge unit found: {ku_results['ids'][0][0]}")
                print(f"  [Agent] Key APIs: {result['key_apis'][:8]}")
            else:
                print("  [Agent] No knowledge unit found.")

        # --- Fallback: Code Examples ---
        if self.use_code and result["ku_code"] == "No reference available.":
            print("  [Agent] Fallback to code examples...")
            code_results = self.rag.search_code(query, n_results=1, tag_filter=intent_tag)
            if code_results["ids"] and code_results["ids"][0]:
                meta = code_results["metadatas"][0][0]
                result["ref_title_fallback"] = meta.get("title", "N/A")
                result["ref_code_fallback"] = meta.get("code_snippet", "")
                if not result["key_apis"]:
                    key_apis_str = meta.get("key_apis", "")
                    result["key_apis"] = [a.strip() for a in key_apis_str.split(",") if a.strip()]
                print(f"  [Agent] Code example found: {code_results['ids'][0][0]}")

        # --- API Docs ---
        if self.use_api:
            print("  [Agent] Reading API documentation...")
            api_docs = []
            try:
                core_pairs = self.rag.get_core_api_docs(limit=30)
                for api_id, doc in core_pairs:
                    api_docs.append(f"--- CORE API: {api_id} ---\n{doc}")
            except Exception as e:
                print(f"  [Agent] Core API injection failed: {e}")

            # Fetch key APIs from retrieval
            if result["key_apis"]:
                try:
                    fetched = self.rag.api_collection.get(ids=result["key_apis"])
                    for i, doc in enumerate(fetched["documents"]):
                        api_docs.append(f"--- API Reference: {fetched['ids'][i]} ---\n{doc}")
                except Exception:
                    pass

            # Semantic search
            search_res = self.rag.search_api(query, n_results=10)
            for doc in search_res["documents"][0]:
                api_docs.append(f"--- API Search Result ---\n{doc}")

            # Dedup
            seen = set()
            deduped = []
            for chunk in api_docs:
                if chunk not in seen:
                    seen.add(chunk)
                    deduped.append(chunk)
            result["api_docs"] = "\n\n".join(deduped)

        return result

    # ------------------------------------------------------------------
    #  Main entry: solve
    # ------------------------------------------------------------------
    def solve(self, user_query, save_code=True, output_dir="code"):
        """
        Run the full pipeline: rewrite → classify → retrieve → generate.

        :param user_query: 用户自然语言查询
        :param save_code: 是否保存生成的代码到文件
        :param output_dir: 代码输出目录
        :return: dict {
            "code": str,              # 生成的 Python 代码
            "intent": str | None,     # 分类标签
            "key_apis": list,         # 检索到的关键 API
            "rewrite": dict,          # query rewriting 各阶段结果
            "file_path": str | None,  # 代码保存路径（如果 save_code）
        }
        """
        print(f"\n{'='*50}")
        print(f"  Agent processing: '{user_query[:80]}{'...' if len(user_query)>80 else ''}'")
        print(f"{'='*50}")

        # --- Step 0: Query Rewriting ---
        rewrite_result = self.rewriter.rewrite(user_query, mode=self.rewrite_mode)
        search_query = rewrite_result["search_query"]
        print(f"  [Rewrite] mode={self.rewrite_mode}, search_query={search_query[:80]}")

        # --- Step 1: Intent Classification ---
        intent_tag = self._classify_intent(user_query)
        print(f"  [Intent] {intent_tag or 'Unclear (Global Search)'}")

        # --- Step 2: Retrieval ---
        retrieval = self._retrieve(search_query, intent_tag)

        # 如果知识单元没找到但有 code fallback，用它
        ref_code = retrieval["ku_code"]
        ref_title = retrieval["ku_title"]
        if ref_code == "No reference available." and retrieval["ref_code_fallback"]:
            ref_code = retrieval["ref_code_fallback"]
            ref_title = retrieval["ref_title_fallback"]

        # --- Step 3: Prompt Construction ---
        user_message = PROMPT_GEN_USER.format(
            query=user_query,
            intent=intent_tag or "General",
            ku_title=ref_title,
            ku_desc=retrieval["ku_desc"],
            ku_code=ref_code,
            api_docs=retrieval["api_docs"],
        )

        messages = [
            {"role": "system", "content": PROMPT_GEN_SYSTEM},
            {"role": "user", "content": user_message},
        ]

        # --- Step 4: Code Generation ---
        print("  [Agent] Generating code (DeepSeek-R1)...")
        response = self.llm.chat(messages, temperature=0.1)

        if not response:
            print("  [Agent] ERROR: LLM returned empty response.")
            return {
                "code": "# Error: Generation failed.",
                "intent": intent_tag,
                "key_apis": retrieval["key_apis"],
                "rewrite": rewrite_result,
                "file_path": None,
            }

        clean_code = self._extract_code(response)
        print(f"  [Agent] Code generated ({len(clean_code)} chars).")

        file_path = None
        if save_code:
            file_path = self.save_generated_code(clean_code, output_dir=output_dir)

        return {
            "code": clean_code,
            "intent": intent_tag,
            "key_apis": retrieval["key_apis"],
            "rewrite": rewrite_result,
            "file_path": file_path,
        }


# ================= CLI =================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genesis RAG Agent — code generation")
    parser.add_argument("--task", type=str, help="User query / task description")
    parser.add_argument(
        "--file", type=str, help="Read task from a text file (first line used)"
    )
    parser.add_argument(
        "--rewrite-mode",
        choices=["none", "translate", "hyde"],
        default="hyde",
        help="Query rewriting mode (default: hyde)",
    )
    parser.add_argument(
        "--output-dir",
        default="code",
        help="Directory to save generated code (default: code/)",
    )
    args = parser.parse_args()

    if not DEEPSEEK_API_KEY:
        print("ERROR: Please set DEEPSEEK_API_KEY in your .env file or environment.")
        sys.exit(1)

    query = None
    if args.task:
        query = args.task
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            query = f.read().strip().split("\n")[0]

    if not query:
        query = input("Enter your query: ").strip()

    if not query:
        print("ERROR: No query provided.")
        sys.exit(1)

    agent = GenesisAgent(rewrite_mode=args.rewrite_mode)
    result = agent.solve(query, save_code=True, output_dir=args.output_dir)

    print("\n" + "=" * 20 + " GENERATED CODE " + "=" * 20)
    print(result["code"])
    print("=" * 56)
    print(f"\nIntent: {result['intent']}")
    print(f"Key APIs: {result['key_apis']}")
    if result["file_path"]:
        print(f"Saved to: {result['file_path']}")

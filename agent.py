"""
Genesis RAG Agent — 基于知识单元检索的代码生成 Agent。

Pipeline:
  1. RAG 检索（通过标准 GenesisRAG.search() 接口）
  2. LLM 生成完整可运行代码

可被 benchmark pipeline 直接 import 调用，也可通过 CLI 独立运行。
"""

import argparse
import json
import os
import re
import sys
import time
import dotenv

# 确保能 import rag_demo 根目录的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_utils import LLMClient
from rag_engine import GenesisRAG
from query_rewriter import QueryRewriter

dotenv.load_dotenv()

# ================= 1. API CONFIGURATION =================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL  = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

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
        rewrite_mode="hyde",
        hyde_route="unit",
    ):
        """
        :param rewrite_mode: "none" / "translate" / "hyde"
        :param hyde_route: "unit" / "fourway"，检索路由
        """
        self.rewrite_mode = rewrite_mode
        self.hyde_route = hyde_route

        # 1. LLM
        self.llm = LLMClient(
            provider="openai",
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_API_URL,
            model=DEEPSEEK_MODEL,
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
    #  knowledge_list → prompt 字段
    # ------------------------------------------------------------------
    @staticmethod
    def _knowledge_list_to_prompt_fields(knowledge_list):
        """
        将 RAG search() 返回的 list[dict] 转为 prompt 模板所需的字段。

        :return: dict {ku_title, ku_desc, ku_code, api_docs, key_apis}
        """
        ku_title = "N/A"
        ku_desc = ""
        ku_code = "No reference available."
        api_docs_parts = []
        key_apis = []

        for item in knowledge_list:
            t = item.get("type", "")
            content = item.get("content", "")
            meta = item.get("meta", {})

            if t == "unit":
                # 第一个 unit 作为主知识单元
                if ku_code == "No reference available.":
                    ku_title = meta.get("title", "N/A")
                    ku_desc = meta.get("desc", "")
                    # 从 content 中提取 code_preview
                    code_match = re.search(r"--- Code Example ---\n(.*)", content, re.DOTALL)
                    ku_code = code_match.group(1).strip() if code_match else content
                    all_apis = meta.get("all_apis", "") or meta.get("key_apis", "")
                    key_apis = [a.strip() for a in all_apis.split(",") if a.strip()]
                else:
                    extra = meta.get("all_apis", "") or meta.get("key_apis", "")
                    for a in extra.split(","):
                        a = a.strip()
                        if a and a not in key_apis:
                            key_apis.append(a)
                api_docs_parts.append(content)

            elif t == "api":
                api_docs_parts.append(content)
                api_id = meta.get("api_id", "")
                if api_id and not meta.get("is_core"):
                    if api_id not in key_apis:
                        key_apis.append(api_id)

            elif t == "code":
                # 代码范例：如果没有知识单元，用它做 fallback
                if ku_code == "No reference available.":
                    code_match = re.search(r"\n(.+)", content, re.DOTALL)
                    ku_code = code_match.group(1).strip() if code_match else content
                    ku_title = meta.get("title", "N/A")
                api_docs_parts.append(content)

            elif t in ("snippet", "error"):
                api_docs_parts.append(content)

        return {
            "ku_title": ku_title,
            "ku_desc": ku_desc,
            "ku_code": ku_code,
            "api_docs": "\n\n".join(api_docs_parts),
            "key_apis": key_apis,
        }

    # ------------------------------------------------------------------
    #  Main entry: solve
    # ------------------------------------------------------------------
    def solve(self, user_query, knowledge_list=None, save_code=True, output_dir="code"):
        """
        Run the full pipeline: (rewrite → classify →) retrieve → generate.

        :param user_query: 用户自然语言查询
        :param knowledge_list: 可选的 RAG 检索结果（list[dict]，来自 pipeline）。
                               如果提供，则跳过 rewrite/classify/retrieve，直接用它生成代码。
                               如果 None，则 agent 内部调 rag.search() 完成检索。
        :param save_code: 是否保存生成的代码到文件
        :param output_dir: 代码输出目录
        :return: dict {
            "code": str,
            "intent": str | None,
            "key_apis": list,
            "rewrite": dict,
            "file_path": str | None,
        }
        """
        print(f"\n{'='*50}")
        print(f"  Agent processing: '{user_query[:80]}{'...' if len(user_query)>80 else ''}'")
        print(f"{'='*50}")

        intent_tag = None
        rewrite_result = {"original": user_query, "search_query": user_query}

        if knowledge_list is None:
            # --- 完整流程：rewrite → classify → search ---
            rewrite_result = self.rewriter.rewrite(user_query, mode=self.rewrite_mode)
            search_query = rewrite_result["search_query"]
            print(f"  [Rewrite] mode={self.rewrite_mode}, search_query={search_query[:80]}")

            intent_tag = self._classify_intent(user_query)
            print(f"  [Intent] {intent_tag or 'Unclear (Global Search)'}")

            knowledge_list = self.rag.search(
                search_query,
                rewrite_mode="none",
                hyde_route=self.hyde_route,
                n_api=6,
                n_code=1,
                n_snippet=3,
                n_error=2,
                n_units=5,
                tag_filter=intent_tag,
                include_core_api=True,
                core_api_limit=40,
            )
            print(f"  [Agent] RAG search returned {len(knowledge_list)} items")
        else:
            print(f"  [Agent] Using provided knowledge_list ({len(knowledge_list)} items)")

        # --- 从 knowledge_list 提取 knowledge_ids（用于检索归因日志）---
        knowledge_ids = []
        for item in knowledge_list:
            meta = item.get("meta", {})
            item_id = meta.get("unit_id") or meta.get("api_id") or meta.get("id") or ""
            if item_id:
                knowledge_ids.append(f"{item.get('type', '?')}:{item_id}")

        # --- 从 knowledge_list 提取 prompt 字段 ---
        fields = self._knowledge_list_to_prompt_fields(knowledge_list)

        # --- Prompt Construction ---
        user_message = PROMPT_GEN_USER.format(
            query=user_query,
            intent=intent_tag or "General",
            ku_title=fields["ku_title"],
            ku_desc=fields["ku_desc"],
            ku_code=fields["ku_code"],
            api_docs=fields["api_docs"],
        )

        messages = [
            {"role": "system", "content": PROMPT_GEN_SYSTEM},
            {"role": "user", "content": user_message},
        ]

        # --- Code Generation ---
        print("  [Agent] Generating code (DeepSeek-R1)...")
        response = self.llm.chat(messages, temperature=0.1)

        if not response:
            print("  [Agent] ERROR: LLM returned empty response.")
            return {
                "code": "# Error: Generation failed.",
                "intent": intent_tag,
                "key_apis": fields["key_apis"],
                "knowledge_ids": knowledge_ids,
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
            "key_apis": fields["key_apis"],
            "knowledge_ids": knowledge_ids,
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
        "--hyde-route",
        choices=["unit", "fourway"],
        default="unit",
        help="Retrieval route (default: unit)",
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

    agent = GenesisAgent(rewrite_mode=args.rewrite_mode, hyde_route=args.hyde_route)
    result = agent.solve(query, save_code=True, output_dir=args.output_dir)

    print("\n" + "=" * 20 + " GENERATED CODE " + "=" * 20)
    print(result["code"])
    print("=" * 56)
    print(f"\nIntent: {result['intent']}")
    print(f"Key APIs: {result['key_apis']}")
    if result["file_path"]:
        print(f"Saved to: {result['file_path']}")

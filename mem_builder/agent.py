import json
import os
import time
import re
import dotenv
from llm_utils import LLMClient
from rag_engine import GenesisRAG

# Load environment variables
dotenv.load_dotenv()

# ================= 1. API CONFIGURATION =================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com")

# ================= 2. DOMAIN CONSTANTS =================
VALID_TAGS = [
    "rigid_body", "soft_body", "fluid_mpm", "fluid_sph", "articulated_robot", 
    "scene_creation", "interaction", "rendering", "camera_control"
]

# ================= 3. PROMPT TEMPLATES =================
# We use Python's .format() syntax using {variable_name} placeholders

# --- Intent Classification Prompt ---
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

# --- Code Generation System Prompt ---
PROMPT_GEN_SYSTEM = """
You are an expert coding assistant for the Genesis Physics Engine.
Generate a complete, runnable Python script based on the User Query.

Priority of truth (highest to lowest):
1) Reference Code Snippet (most important): copy its overall structure and API usage patterns.
2) API Docs: use as a hint for names and available attributes; it may be incomplete.
3) Your own guesses: NOT allowed.

Hard rules (must follow):
- Output MUST be runnable Python (no pseudo-code).
- Always initialize with `gs.init()` and create a `gs.Scene(...)`.
- DO NOT invent APIs, attributes, enum values, or parameters.
  If an option/argument/attribute is not shown in the Reference Code Snippet AND not present in API Docs, DO NOT use it.
- Prefer defaults: if the user did not explicitly ask for advanced solver/options tuning, do not set those fields at all.
  (Example: do not set `rigid_options.constraint_solver` unless explicitly required. If unsure, omit and use default.)
- Keep calls minimal: pass only the minimum necessary arguments that appear in the Reference Code Snippet / API Docs.
- If there is a conflict between Reference Code and API Docs, follow the Reference Code and simplify (omit the conflicting argument).

Common hallucination traps to avoid:
- Enums: never use enum members that are not explicitly listed in API Docs / reference.
  For example, `gs.constraint_solver` only supports its real members (e.g., `CG`, `Newton`); do not use made-up values like `SAP`.
- Modules vs callables: some names are modules (e.g., `gs.materials.FEM`) and are not callable; use concrete classes/functions.

Self-check before finalizing:
- Scan your code for any dotted attribute like `gs.xxx.yyy`. If you cannot point to it in the Reference Code Snippet or API Docs, remove it.
- If you added optional config/options, try deleting them unless the user requested them.
"""

# --- Code Generation User Prompt ---
PROMPT_GEN_USER = """
User Query: {query}

--- Reference Example ({intent}) ---
Title: {ref_title}
Snippet:
{ref_code}

--- API Documentation (Reference) ---
{api_docs}
{snippets_block}
{errors_block}

Task:
- Write the full Python code for the user query.
- Follow the Reference Example's structure and style as much as possible.
- Use API Docs only as a reference; if something is missing/unclear, prefer the Reference Example and keep it minimal.
- Avoid advanced options unless the user asked for them; defaults are preferred.

Output format:
- Output ONLY the Python code (no markdown fences, no explanations).
"""


# ================= 4. RETRIEVAL SWITCHES =================
# 是否启用各知识库检索：API / 完整代码范例 / 代码片段 默认 True，错误记忆默认 False
# 构造 Agent 时可覆盖，例如: GenesisAgent(use_errors=True) 开启错误记忆检索
USE_API = True
USE_CODE = True
USE_SNIPPETS = True
USE_ERRORS = False

# ================= 5. AGENT LOGIC =================
class GenesisAgent:
    def __init__(self, use_api=USE_API, use_code=USE_CODE, use_snippets=USE_SNIPPETS, use_errors=USE_ERRORS):
        """
        use_api: 是否检索 API 文档（含 core 注入）
        use_code: 是否检索完整代码范例
        use_snippets: 是否检索代码片段
        use_errors: 是否检索错误记忆（默认关闭）
        """
        self.use_api = use_api
        self.use_code = use_code
        self.use_snippets = use_snippets
        self.use_errors = use_errors

        # 1. Initialize Brain (LLM)
        self.llm = LLMClient(
            provider="openai",
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_API_URL,
            model="deepseek-reasoner"
        )

        # 2. Initialize Memory (RAG Engine)
        self.rag = GenesisRAG(reset_db=False)

    def _classify_intent(self, query):
        """[Slow Thinking] Classify user intent."""
        # Fill the template
        prompt = PROMPT_CLASSIFY_INTENT.format(
            tags_json=json.dumps(VALID_TAGS),
            query=query
        )
        
        try:
            # Low temperature for deterministic classification
            response = self.llm.chat([{"role": "user", "content": prompt}], temperature=0.01)
            
            if not response: 
                return None
            
            tag = response.strip().replace("'", "").replace('"', "")
            if tag in VALID_TAGS:
                return tag
            return None
        except Exception:
            return None

    def save_generated_code(self, code_content):
        """Save generated code to local file with UTF-8 encoding."""
        output_dir = "code"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"agent_code_{timestamp}.py"
        file_path = os.path.join(output_dir, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code_content)
            
        print(f"💾 Code saved to: {file_path}")
        return file_path

    def solve(self, user_query):
        print(f"\n🤖 Agent is thinking about: '{user_query}' ...")
        
        # --- Step 0: Slow Thinking (Intent Classification) ---
        intent_tag = self._classify_intent(user_query)
        print(f"   🧠 [Intent] Identified: {intent_tag if intent_tag else 'Unclear (Global Search)'}")

        ref_title = "N/A"
        ref_code = "No reference available."
        key_apis = []

        # --- Step 1: Code Retrieval（完整代码范例）---
        if self.use_code:
            print("   🔍 Searching for reference examples (code)...")
            code_results = self.rag.search_code(user_query, n_results=1, tag_filter=intent_tag)
            if code_results['ids'][0]:
                meta = code_results['metadatas'][0][0]
                ref_title = meta.get('title', 'N/A')
                ref_code = meta.get("code_snippet", "")
                key_apis_str = meta.get("key_apis", "")
                key_apis = key_apis_str.split(",") if key_apis_str else []
                print(f"   💡 Reference Found: {code_results['ids'][0][0]}")
                print(f"   🗝️  Key APIs: {key_apis}")
            else:
                print("   ⚠️ No reference found. Generating from scratch.")
        else:
            print("   ⏭️ Code retrieval disabled.")

        # --- Step 2: API Retrieval ---
        api_docs = []
        if self.use_api:
            print("   📖 Reading API documentation...")
            try:
                core_pairs = self.rag.get_core_api_docs(limit=30)
                for api_id, doc in core_pairs:
                    api_docs.append(f"--- CORE API: {api_id} ---\n{doc}")
            except Exception as e:
                print(f"   ⚠️ Core API 注入失败（将继续）：{e}")
            if key_apis:
                fetched = self.rag.api_collection.get(ids=key_apis)
                for i, doc in enumerate(fetched['documents']):
                    api_docs.append(f"--- API Reference: {fetched['ids'][i]} ---\n{doc}")
            search_res = self.rag.search_api(user_query, n_results=10)
            for doc in search_res['documents'][0]:
                api_docs.append(f"--- API Search Result ---\n{doc}")
            deduped = []
            seen = set()
            for chunk in api_docs:
                if chunk in seen:
                    continue
                seen.add(chunk)
                deduped.append(chunk)
            api_docs = deduped
        else:
            print("   ⏭️ API retrieval disabled.")
        context_str = "\n\n".join(api_docs)

        # --- Step 2b: Snippets Retrieval（代码片段）---
        snippets_block = ""
        if self.use_snippets:
            print("   📎 Searching for code snippets...")
            try:
                snip_res = self.rag.search_snippet(user_query, n_results=3, tag_filter=intent_tag)
                if snip_res['ids'][0]:
                    parts = []
                    for j, sid in enumerate(snip_res['ids'][0]):
                        meta = snip_res['metadatas'][0][j]
                        task = meta.get('task', '')
                        code = meta.get('code', '')
                        parts.append(f"[Snippet {j+1}] Task: {task}\n{code}")
                    snippets_block = "\n\n--- Code Snippets (Reference) ---\n" + "\n\n".join(parts)
                else:
                    snippets_block = ""
            except Exception as e:
                print(f"   ⚠️ Snippet retrieval failed: {e}")
        else:
            print("   ⏭️ Snippet retrieval disabled.")

        # --- Step 2c: Error Memory Retrieval（错误记忆，默认关闭）---
        errors_block = ""
        if self.use_errors:
            print("   🚫 Searching for error memory...")
            try:
                err_res = self.rag.search_error(user_query, n_results=3)
                if err_res['ids'][0]:
                    parts = []
                    for j, eid in enumerate(err_res['ids'][0]):
                        meta = err_res['metadatas'][0][j]
                        bad = meta.get('bad_pattern', '')
                        corr = meta.get('correction', '')
                        exp = meta.get('explanation', '')
                        parts.append(f"Bad: {bad} → Correction: {corr}. Explanation: {exp}")
                    errors_block = "\n\n--- Error Memory (Avoid these patterns) ---\n" + "\n".join(parts)
                else:
                    errors_block = ""
            except Exception as e:
                print(f"   ⚠️ Error memory retrieval failed: {e}")
        else:
            pass  # 默认不打印，避免刷屏

        # --- Step 3: Prompt Construction ---
        user_message = PROMPT_GEN_USER.format(
            query=user_query,
            intent=intent_tag if intent_tag else 'General',
            ref_title=ref_title,
            ref_code=ref_code,
            api_docs=context_str,
            snippets_block=snippets_block,
            errors_block=errors_block,
        )

        messages = [
            {"role": "system", "content": PROMPT_GEN_SYSTEM},
            {"role": "user", "content": user_message}
        ]

        ## 输出user_message
        print(f"user_message:{user_message}")
        
        # --- Step 4: Code Generation ---
        print("   ✍️  Generating code (DeepSeek-R1 is thinking)...")
        response = self.llm.chat(messages, temperature=0.1)
        
        if not response:
            print("❌ Error: LLM returned empty response.")
            return "Error: Generation failed."

        # Regex Extraction
        pattern = r"```(?:python)?\s*(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            clean_code = match.group(1).strip()
            print("   ✂️  Extracted code from markdown.")
        else:
            print("   ⚠️  Markdown not found, using raw text.")
            clean_code = response.replace("```python", "").replace("```", "").strip()

        # Save & Return
        self.save_generated_code(clean_code)
        return clean_code

if __name__ == "__main__":
    if not DEEPSEEK_API_KEY:
        print("❌ Error: Please set DEEPSEEK_API_KEY in your .env file or environment.")
    else:
        agent = GenesisAgent()
        
        # Test Case
        # query = "A soft blue sphere crashed onto the ground."
        query = "生成一个绿色胶体小球和蓝色液体小球碰撞的视频。胶体球从上方落下，液体球静止在下方。"
        code = agent.solve(query)
        
        print("\n" + "="*20 + " GENERATED CODE " + "="*20)
        print(code)
        print("="*56)
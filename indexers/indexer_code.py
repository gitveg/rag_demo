import os
import sys
import json
import ast
from typing import Dict, FrozenSet, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_utils import LLMClient
from api_id_normalize import resolve_api_to_known, normalize_api_id_for_kb
from tqdm import tqdm

# ================= 配置区域 =================
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KB_DIR   = os.path.join(_BASE_DIR, "knowledge_base")

EXAMPLES_DIR = os.path.join(_BASE_DIR, "examples")
OUTPUT_FILE  = os.path.join(_KB_DIR,   "genesis_code_index.json")
API_KB_FILE  = os.path.join(_KB_DIR,   "genesis_knowledge_base_final.json")

# --- 1. 统一标签池 (扁平化) ---
# 混合了物理类型和任务类型，供 LLM 选择
ALLOWED_TAGS = [
    # Physics (What is it?)
    "rigid_body", "soft_body", "fluid_mpm", "fluid_sph", "articulated_robot", "mixed_physics",
    # Task (What does it do?)
    "scene_creation", "motion_planning", "interaction", "rendering", "camera_control", 
    "vis_export", "depth_sensing", "tactile_sensing"
]

# --- 2. Prompt ---
SYSTEM_PROMPT = f"""
You are a Code Analysis Agent for Genesis Physics Engine.
Analyze the script and generate concise metadata.

Input: Python source code.

Output Requirements:
1. "title": Human-readable title (e.g., "Franka Arm Grasping").
2. "description": 1 sentence summary of the logic (e.g., "Uses IK to control a Franka arm to grasp a box.").
3. "tags": A list of strings selected ONLY from: {json.dumps(ALLOWED_TAGS)}. Select 1-3 most relevant tags.

Response Format: Pure JSON.
"""

# ================= AST 分析器 =================
class GenesisImportVisitor(ast.NodeVisitor):
    """
    提取 genesis.* API 引用。
    除 gs.morphs.Sphere 等静态链外，通过「构造绑定」解析 scene.add_entity → genesis.Scene.add_entity：
    变量被赋值为 KB 中标记为 class 的构造调用（如 gs.Scene(...)）时，记录 var → 该类的 api_id。
    """

    def __init__(self, kb_class_ids: FrozenSet[str]):
        self.api_calls: set = set()
        self.imports: Dict[str, str] = {}
        self.kb_class_ids = kb_class_ids
        self.scope_stack: List[Dict[str, str]] = [{}]

    def _scope(self) -> Dict[str, str]:
        return self.scope_stack[-1]

    def _var_type_prefix(self, name: str) -> Optional[str]:
        for frame in reversed(self.scope_stack):
            if name in frame:
                return frame[name]
        return None

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == 'genesis':
                self.imports[alias.asname or 'genesis'] = 'genesis'
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.startswith('genesis'):
            for alias in node.names:
                self.imports[alias.asname or alias.name] = f"{node.module}.{alias.name}"
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.scope_stack.append({})
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node):
        self.scope_stack.append({})
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_ClassDef(self, node):
        self.scope_stack.append({})
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Assign(self, node):
        ctype = None
        if isinstance(node.value, ast.Call):
            ctype = self._constructor_class_api_id(node.value)
        sc = self._scope()
        for t in node.targets:
            if isinstance(t, ast.Name):
                if ctype:
                    sc[t.id] = ctype
                else:
                    sc.pop(t.id, None)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if node.value is not None and isinstance(node.value, ast.Call):
            ctype = self._constructor_class_api_id(node.value)
            if isinstance(node.target, ast.Name):
                sc = self._scope()
                if ctype:
                    sc[node.target.id] = ctype
                else:
                    sc.pop(node.target.id, None)
        self.generic_visit(node)

    def _constructor_class_api_id(self, call: ast.Call) -> Optional[str]:
        fn = call.func
        base = None
        if isinstance(fn, ast.Attribute):
            base = self._get_full_name(fn)
        elif isinstance(fn, ast.Name):
            base = self.imports.get(fn.id)
        if base and base in self.kb_class_ids:
            return base
        return None

    def _get_full_name(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Attribute):
            prefix = self._get_full_name(node.value)
            if prefix:
                return f"{prefix}.{node.attr}"
            if isinstance(node.value, ast.Name):
                vbase = self._var_type_prefix(node.value.id)
                if vbase:
                    return f"{vbase}.{node.attr}"
            return None
        if isinstance(node, ast.Name):
            if node.id in self.imports:
                return self.imports[node.id]
        return None

    def visit_Attribute(self, node):
        full_name = self._get_full_name(node)
        if full_name and full_name.startswith("genesis."):
            self.api_calls.add(full_name)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            full_name = self._get_full_name(node.func)
            if full_name and full_name.startswith("genesis."):
                self.api_calls.add(full_name)
        elif isinstance(node.func, ast.Name):
            base = self.imports.get(node.func.id)
            if base and base.startswith("genesis."):
                self.api_calls.add(base)
        self.generic_visit(node)

# ================= 主程序 =================
def build_code_index():
    # 1. 初始化 LLM
    llm = LLMClient(
        provider="openai",
        api_key="sk-061e03c70f63402bb363bcd2960622d2", # 请确保 Key 正确
        base_url="https://api.deepseek.com",
        model="deepseek-chat"
    )

    # 2. 加载知识库白名单 + 可构造类 id（用于 scene.add_entity 等实例方法解析）
    #    以及 core API 集合（用于 all_apis/key_apis 分层）
    known_apis = set()
    core_apis = set()
    kb_class_ids = frozenset()
    if os.path.exists(API_KB_FILE):
        with open(API_KB_FILE, 'r', encoding='utf-8') as f:
            api_data = json.load(f)
            known_apis = set(item['api_id'] for item in api_data)
            core_apis = set(
                item['api_id']
                for item in api_data
                if item.get('api_id') and ('core' in (item.get('domain_tags') or []))
            )
            kb_class_ids = frozenset(
                item['api_id']
                for item in api_data
                if item.get('type') == 'class' and item.get('api_id')
            )
        print(f"📚 已加载白名单，包含 {len(known_apis)} 个标准 API。")
        print(f"📚 其中 core API {len(core_apis)} 个。")
        print(f"📚 其中 class 条目 {len(kb_class_ids)} 个（用于构造绑定）。")
    else:
        print("⚠️ 未找到知识库，将跳过白名单校验。")

    # 3. 扫描文件
    script_files = []
    if os.path.exists(EXAMPLES_DIR):
        for root, dirs, files in os.walk(EXAMPLES_DIR):
            for file in files:
                if file.endswith(".py"):
                    script_files.append(os.path.join(root, file))
    else:
        print(f"❌ 错误: 找不到范例目录 '{EXAMPLES_DIR}'")
        return

    # 建议先切片测试前 5 个，正式跑时去掉 [:5]
    # process_files = script_files[:5]
    process_files = script_files
    
    print(f"🚀 开始构建范例库 (Target: {len(process_files)} files)...")
    
    cookbook = []

    for file_path in tqdm(process_files, desc="Indexing Code"):
        file_name = os.path.basename(file_path)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code_content = f.read()

            # --- A. AST 静态提取 Key APIs ---
            tree = ast.parse(code_content)
            visitor = GenesisImportVisitor(kb_class_ids)
            visitor.visit(tree)
            
            raw_apis = list(visitor.api_calls)
            filtered_apis = []

            for api in raw_apis:
                if known_apis:
                    canonical = resolve_api_to_known(api, known_apis)
                    if canonical is None:
                        continue
                else:
                    canonical = normalize_api_id_for_kb(api)
                filtered_apis.append(canonical)
            
            # 去重并排序：all_apis 保留完整命中；key_apis 去掉 core API，突出任务关键信号
            all_apis = sorted(list(set(filtered_apis)))
            key_apis = [api for api in all_apis if api not in core_apis]

            # --- B. LLM 语义分析 ---
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": code_content[:4000]} # 截断
            ]
            
            try:
                response = llm.chat(messages, temperature=0.1)
                response = response.replace("```json", "").replace("```", "").strip()
                meta_data = json.loads(response)
            except Exception:
                meta_data = {}

            # --- C. 组装 v2.0 Schema ---
            entry = {
                "id": file_name, # 文件名即 ID
                "code": code_content,
                "metadata": {
                    "title": meta_data.get("title", file_name),
                    "desc": meta_data.get("description", "No description."),
                    "tags": meta_data.get("tags", []),
                    "all_apis": all_apis,  # 全量 Genesis API（含 core）
                    "key_apis": key_apis  # 关键 API（all_apis 去除 core 后）
                }
            }
            
            cookbook.append(entry)

        except Exception as e:
            tqdm.write(f"❌ Error processing {file_name}: {e}")

    # 4. 保存
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cookbook, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 构建完成！范例库已保存至: {OUTPUT_FILE}")
    if cookbook:
        print("🔎 Sample Entry:")
        print(json.dumps(cookbook[0]["metadata"], indent=2))

if __name__ == "__main__":
    build_code_index()

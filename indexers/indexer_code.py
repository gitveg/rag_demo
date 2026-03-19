import os
import sys
import json
import ast
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_utils import LLMClient
from tqdm import tqdm

# ================= 配置区域 =================
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KB_DIR   = os.path.join(_BASE_DIR, "knowledge_base")

EXAMPLES_DIR = os.path.join(_BASE_DIR, "examples")
OUTPUT_FILE  = os.path.join(_KB_DIR,   "genesis_code_index.json")
API_KB_FILE  = os.path.join(_KB_DIR,   "genesis_knowledge_base_final.json")

# --- 1. 高频 API 停用词表 (Stop Words) ---
# 这些 API 出现在几乎所有范例中，对检索没有区分度，必须剔除
COMMON_API_BLOCKLIST = {
    "genesis.init",
    "genesis.Scene",           # 只是类名，太泛
    "genesis.Scene.__init__",
    "genesis.Scene.build",     # 必调用的
    "genesis.Scene.step",      # 必调用的
    "genesis.Scene.reset",
}

# --- 2. 统一标签池 (扁平化) ---
# 混合了物理类型和任务类型，供 LLM 选择
ALLOWED_TAGS = [
    # Physics (What is it?)
    "rigid_body", "soft_body", "fluid_mpm", "fluid_sph", "articulated_robot", "mixed_physics",
    # Task (What does it do?)
    "scene_creation", "motion_planning", "interaction", "rendering", "camera_control", 
    "vis_export", "depth_sensing", "tactile_sensing"
]

# --- 3. Prompt ---
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
    def __init__(self):
        self.api_calls = set()
        self.imports = {} 

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
        self.generic_visit(node)

    def _get_full_name(self, node):
        if isinstance(node, ast.Attribute):
            prefix = self._get_full_name(node.value)
            if prefix: return f"{prefix}.{node.attr}"
        elif isinstance(node, ast.Name):
            if node.id in self.imports:
                return self.imports[node.id]
        return None

# ================= 主程序 =================
def build_code_index():
    # 1. 初始化 LLM
    llm = LLMClient(
        provider="openai",
        api_key="sk-061e03c70f63402bb363bcd2960622d2", # 请确保 Key 正确
        base_url="https://api.deepseek.com",
        model="deepseek-chat"
    )

    # 2. 加载知识库白名单
    known_apis = set()
    if os.path.exists(API_KB_FILE):
        with open(API_KB_FILE, 'r', encoding='utf-8') as f:
            api_data = json.load(f)
            known_apis = set(item['api_id'] for item in api_data)
        print(f"📚 已加载白名单，包含 {len(known_apis)} 个标准 API。")
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
            visitor = GenesisImportVisitor()
            visitor.visit(tree)
            
            raw_apis = list(visitor.api_calls)
            filtered_apis = []

            for api in raw_apis:
                # 过滤器 1: 必须在 API 知识库里 (保证是正规军)
                if known_apis and api not in known_apis:
                    continue
                # 过滤器 2: 不能是高频停用词 (保证是关键特征)
                if api in COMMON_API_BLOCKLIST:
                    continue
                
                filtered_apis.append(api)
            
            # 去重并排序
            key_apis = sorted(list(set(filtered_apis)))

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
                    "key_apis": key_apis  # 这里的 API 都是“干货”
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

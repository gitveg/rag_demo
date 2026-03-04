import os
import ast
import json
import hashlib
from collections import defaultdict
import dotenv
from tqdm import tqdm

# 加载环境变量 (如果需要最后一步AI标注)
from utils.llm_client import LLMClient 
dotenv.load_dotenv()

# ================= 配置 =================
SOURCE_DIR = "./RAG/examples"  # 官方 Examples 文件夹
OUTPUT_FILE = "./RAG/genesis_code_snippets.json"

# ================= 人工手动添加的代码片段 =================
# 这些片段不会从 examples 中 AST 提取，在 build 时直接合并进最终 snippets，保证 RAG 能检索到。
MANUAL_SNIPPETS = [
    {
        "id": "snip_manual_camera_recording",
        "task": "Record simulation to video with camera: start_recording, step loop with set_pose and render, then stop_recording(save_to_filename=..., fps=...).",
        "code": """cam.start_recording()

import numpy as np
for i in range(120):
    scene.step()

    cam.set_pose(
        pos    = (3.0 * np.sin(i / 60), 3.0 * np.cos(i / 60), 2.5),
        lookat = (0, 0, 0.5),
    )

    cam.render()

cam.stop_recording(save_to_filename='video.mp4', fps=60)""",
        "key_apis": ["start_recording", "stop_recording", "set_pose", "render", "camera_recording"],
        "tags": ["manual_added", "recording", "video"],
    },
]

# ================= 1. 智能 AST 分析器 =================
class GenesisVisitor(ast.NodeVisitor):
    def __init__(self, source_code):
        self.source_code = source_code
        self.snippets = [] 
        
        # 核心逻辑：动态追踪变量名
        self.genesis_alias = None      # 存 'gs' 或 'genesis'
        self.genesis_vars = set()      # 存 ['scene', 'plane', 'morph', ...] 只要是 Genesis 对象

    def visit_Import(self, node):
        """1. 侦测 import genesis as ..."""
        for alias in node.names:
            if alias.name == 'genesis':
                self.genesis_alias = alias.asname if alias.asname else 'genesis'
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """处理 from genesis import ... (虽然官方例子较少用，但为了健壮性)"""
        if node.module == 'genesis':
            # 如果直接 from genesis import Scene，把 Scene 加入追踪列表
            for alias in node.names:
                var_name = alias.asname if alias.asname else alias.name
                self.genesis_vars.add(var_name)
        self.generic_visit(node)

    def visit_Assign(self, node):
        """2. 变量血缘追踪：如果右边是 Genesis 对象，左边的变量也标记为 Genesis 对象"""
        self.generic_visit(node)
        
        # 简单的右值检查 logic
        is_genesis_source = False
        
        # 检查右边是否是调用: scene = gs.Scene()
        if isinstance(node.value, ast.Call):
            func = node.value.func
            # 情况 A: gs.Scene() -> Attribute
            if isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name) and func.value.id == self.genesis_alias:
                    is_genesis_source = True
            # 情况 B: Scene() (from genesis import Scene)
            elif isinstance(func, ast.Name) and func.id in self.genesis_vars:
                is_genesis_source = True
        
        # 如果来源确定是 Genesis，把左边的变量名加入“家族名单”
        if is_genesis_source:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.genesis_vars.add(target.id)
            
            # 同时，这也是一个值得提取的片段 (对象创建)
            self._extract_snippet(node)

    def visit_Call(self, node):
        """3. 提取调用：只要调用者是 Genesis 家族的，就提取"""
        self.generic_visit(node)
        
        should_extract = False
        
        func = node.func
        # 情况 A: gs.options.SimOptions(...)
        if isinstance(func, ast.Attribute):
            # 检查前缀: gs.xxx
            if isinstance(func.value, ast.Name) and func.value.id == self.genesis_alias:
                should_extract = True
            # 检查变量: scene.add_entity(...)，且 scene 在家族名单里
            elif isinstance(func.value, ast.Name) and func.value.id in self.genesis_vars:
                should_extract = True
            # 链式调用: gs.morphs.Box().set_pos() - 这种稍微复杂，暂且通过根节点判断
            
        if should_extract:
            self._extract_snippet(node)

    def _extract_snippet(self, node):
        """通用提取逻辑"""
        try:
            segment = ast.get_source_segment(self.source_code, node)
            if not segment: return
            snippet_clean = segment.strip()
            
            # 获取 API 名称作为归类 Key
            api_key = "unknown"
            if isinstance(node, ast.Call):
                # 尝试解析 gs.Scene 这种名字
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    api_key = f"{node.func.value.id}.{node.func.attr}" # e.g. gs.Scene
                elif isinstance(node.func, ast.Attribute):
                     api_key = node.func.attr # e.g. add_entity (简化处理)
            elif isinstance(node, ast.Assign):
                 api_key = "assignment"

            # 替换掉具体的变量名，归一化 key (比如把 scene.add 归类为 .add)
            # 这一步是为了后续聚合，不用太精确，因为有去重逻辑兜底
            
            # 简单的复杂度计算
            complexity = len(snippet_clean)
            if isinstance(node, ast.Call):
                complexity += len(node.args) * 5 + len(node.keywords) * 5

            self.snippets.append({
                "code": snippet_clean,
                "complexity": complexity,
                "raw_api_key": api_key 
            })
        except:
            pass

# ================= 2. 主处理流程 (保持不变的去重逻辑) =================

def normalize_code(code_str):
    return "".join(code_str.split())

def build_snippets_db():
    print(f"📂 Scanning examples in {SOURCE_DIR}...")
    
    all_raw_snippets = []
    
    file_list = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.py')]
    
    for fname in tqdm(file_list, desc="Parsing Files"):
        path = os.path.join(SOURCE_DIR, fname)
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        try:
            tree = ast.parse(source)
            visitor = GenesisVisitor(source) # 使用新的智能 Visitor
            visitor.visit(tree)
            all_raw_snippets.extend(visitor.snippets)
        except Exception as e:
            print(f"⚠️ Error parsing {fname}: {e}")

    print(f"🔍 Found {len(all_raw_snippets)} raw calls. Deduplicating...")

    # --- 聚类策略 ---
    # 因为我们去掉了 Prefix，现在所有调用都混在一起。
    # 我们需要根据代码的相似度或者 API 关键词进行简单的聚类，
    # 否则 "scene.add" 和 "gs.Scene" 会混在一起筛选。
    
    # 策略：按代码中的核心关键词聚类 (Key API)
    clustered = defaultdict(list)
    for s in all_raw_snippets:
        code = s['code']
        # 提取特征词：比如 "gs.Scene", "add_entity", "SimOptions"
        # 简单的正则或 split 即可
        if "gs." in code:
            # 提取 gs.xxx.yyy
            start = code.find("gs.")
            end = code.find("(", start)
            if end != -1:
                key = code[start:end].strip() # gs.Scene
            else:
                key = "gs_general"
        elif ".add_entity" in code:
            key = "add_entity"
        elif ".options" in code:
            key = "options"
        else:
            # 实在分不出来的，按 raw_api_key
            key = s['raw_api_key']
            
        clustered[key].append(s)

    final_snippets = []
    
    # --- 筛选策略 (保留 Simple, Medium, Complex) ---
    for api_key, items in clustered.items():
        if len(items) == 0: continue
        
        # 1. 指纹去重
        unique_map = {}
        for it in items:
            h = hashlib.md5(normalize_code(it['code']).encode()).hexdigest()
            if h not in unique_map:
                unique_map[h] = it
        
        candidates = list(unique_map.values())
        candidates.sort(key=lambda x: x['complexity'])
        
        # 2. 采样
        selected = []
        count = len(candidates)
        if count <= 3:
            selected = candidates
        else:
            selected = [candidates[0], candidates[count//2], candidates[-1]]
            
        for s in selected:
            final_snippets.append({
                "id": f"snip_{hashlib.md5(s['code'].encode()).hexdigest()[:8]}",
                "task": f"Usage example of {api_key}", # 暂存，后面 AI 会修
                "code": s['code'],
                "key_apis": [api_key],
                "tags": ["auto_extracted"]
            })

    print(f"✅ Final Snippets Count: {len(final_snippets)}")
    return final_snippets

# ================= 3. AI 标注 (逻辑复用) =================
def enrich_with_llm(snippets):
    """(保持原样)"""
    if not snippets: return []
    print("🧠 Enriching snippets with LLM...")
    # ... 这里复用之前的 LLM 代码 ...
    # 为了演示简洁，此处省略具体 LLM 调用代码，直接返回
    return snippets

if __name__ == "__main__":
    snippets = build_snippets_db()

    # 合并人工手动添加的片段（避免与自动提取的 id 重复）
    existing_ids = {s["id"] for s in snippets}
    for manual in MANUAL_SNIPPETS:
        if manual["id"] not in existing_ids:
            snippets.append(manual)
            existing_ids.add(manual["id"])
    if MANUAL_SNIPPETS:
        print(f"   📌 已合并 {len(MANUAL_SNIPPETS)} 个人工添加片段 (MANUAL_SNIPPETS)")

    # 记得把这行取消注释，真正跑的时候需要 LLM 润色 Task 描述
    # snippets = enrich_with_llm(snippets)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(snippets, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved to {OUTPUT_FILE}")
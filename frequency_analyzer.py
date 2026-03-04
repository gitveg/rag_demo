import os
import ast
import json
import collections
from pathlib import Path

# 设定范例文件夹路径
EXAMPLES_DIR = "examples" 
OUTPUT_FILE = "api_frequency_report.json"

class GenesisVisitor(ast.NodeVisitor):
    """
    AST 遍历器：专门提取 genesis 相关的属性访问和函数调用
    """
    def __init__(self):
        self.api_calls = []
        self.imports = {} # 记录别名映射，例如 {'gs': 'genesis'}

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == 'genesis':
                self.imports[alias.asname or 'genesis'] = 'genesis'
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.startswith('genesis'):
            for alias in node.names:
                # 记录 from genesis import Scene 这种情况
                self.imports[alias.asname or alias.name] = f"{node.module}.{alias.name}"
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # 捕捉 gs.Scene, gs.morphs.Box 这种链式调用
        full_name = self._get_full_name(node)
        if full_name:
            self.api_calls.append(full_name)
        self.generic_visit(node)

    def visit_Call(self, node):
        # 捕捉函数调用，主要是为了强化权重
        # 这里我们复用 visit_Attribute 的逻辑，但在统计时可以考虑加权
        if isinstance(node.func, ast.Attribute):
            full_name = self._get_full_name(node.func)
            if full_name:
                self.api_calls.append(full_name)
        self.generic_visit(node)

    def _get_full_name(self, node):
        """递归解析属性链，如 gs.morphs.Box"""
        if isinstance(node, ast.Attribute):
            prefix = self._get_full_name(node.value)
            if prefix:
                return f"{prefix}.{node.attr}"
        elif isinstance(node, ast.Name):
            # 检查这个名字是否是 genesis 的别名
            if node.id in self.imports:
                # 如果是 import genesis as gs，返回 genesis
                if self.imports[node.id] == 'genesis':
                    return 'genesis'
                # 如果是 from genesis import Scene，返回 genesis.Scene
                return self.imports[node.id]
        return None

def analyze_frequency():
    print(f"🚀 开始扫描 {EXAMPLES_DIR} 目录下的范例代码...")
    
    if not os.path.exists(EXAMPLES_DIR):
        print(f"❌ 错误: 找不到文件夹 '{EXAMPLES_DIR}'")
        return

    total_files = 0
    all_calls = []

    # 1. 遍历所有 .py 文件
    for root, dirs, files in os.walk(EXAMPLES_DIR):
        for file in files:
            if file.endswith(".py"):
                total_files += 1
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                    
                    visitor = GenesisVisitor()
                    visitor.visit(tree)
                    
                    # 过滤：只保留以 genesis 开头的调用
                    valid_calls = [c for c in visitor.api_calls if c.startswith("genesis.")]
                    all_calls.extend(valid_calls)
                    
                except Exception as e:
                    print(f"   ⚠️ 解析失败: {file} - {e}")

    # 2. 统计频率
    counter = collections.Counter(all_calls)
    
    # 3. 格式化报告
    report = []
    for api, count in counter.most_common():
        # 简单的归一化得分 (0-100)
        score = round((count / total_files) * 100, 2)
        
        # 自动打标建议
        tag = "core" if score > 50 else ("common" if score > 10 else "rare")
        
        report.append({
            "api_name": api,
            "count": count,
            "frequency_score": score, # 出现频率 (百分比)
            "suggested_tag": tag
        })

    # 4. 保存
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ 分析完成！扫描了 {total_files} 个文件。")
    print(f"📊 发现 {len(report)} 个不同的 API 调用。")
    print(f"💾 报告已保存至: {OUTPUT_FILE}")
    
    # 打印 Top 10 预览
    print("\n🔥 Top 10 最热 API:")
    for item in report[:10]:
        print(f"   {item['api_name']:<40} | 次数: {item['count']} | 覆盖率: {item['frequency_score']}%")

if __name__ == "__main__":
    analyze_frequency()
import griffe
import json

# 加载 Genesis 库进行分析
# 假设 genesis 是已安装的包名，或者你可以指向其源码路径
genesis_pkg = griffe.load("Genesis-main/genesis") 

knowledge_base = []

# 递归遍历所有模块、类、函数
for name, member in genesis_pkg.members.items():
    # 只提取类和函数
    if member.is_class or member.is_function:
        entry = {
            "name": member.path,  # 例如 genesis.engine.Step
            "type": member.kind.value,
            # 提取文档字符串
            "doc": member.docstring.value if member.docstring else "",
            # 这一步是关键：直接把函数签名转成字符串，Agent 一眼就能看懂怎么调用
            # Griffe 提供了很方便的 parameters 访问
            "parameters": str(member.parameters) if hasattr(member, "parameters") else ""
        }
        knowledge_base.append(entry)

# 保存为 jsonl 文件，准备做 Embedding
with open("genesis_kb_for_rag.jsonl", "w", encoding="utf-8") as f:
    for entry in knowledge_base:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

print(f"提取完成，共生成 {len(knowledge_base)} 条知识条目")
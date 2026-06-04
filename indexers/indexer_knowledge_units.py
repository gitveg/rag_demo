"""
知识单元构建器（Knowledge Unit Indexer）

策略：以代码文件为核心，将每个代码范例与其 key_apis 对应的 API 文档聚合，
形成自洽的"知识单元"，专为 HyDE 检索优化。

HyDE 对齐原理：
  - HyDE 生成的伪代码（如 scene.add_entity(morph=gs.morphs.Sphere(...))）
    和真实代码文件在 embedding 空间天然对齐。
  - 每个知识单元的 embedding_text 设计为"代码风格 header + 代码预览"，
    与 HyDE 伪代码语义空间一致，检索精度显著优于 API 文档向量。

输入：
  - genesis_api_index.json  （API 知识库）
  - genesis_code_index.json            （代码范例库）
  两者均位于 phys_agent/RAG/ 目录。

输出：
  - genesis_knowledge_units.json       （知识单元库，写入 phys_agent/RAG/）
    每条记录包含：
      unit_id        : 唯一 ID（来自文件名，去掉 .py）
      title          : 范例标题
      desc           : 范例描述
      tags           : 领域标签列表（rigid_body / soft_body / ...）
      key_apis       : 该范例使用的关键 Genesis API 列表
      api_docs       : 对应 API 文档的精简摘要列表（供 LLM 消费）
      code           : 完整代码
      embedding_text : 用于向量化的代码风格聚合文本（HyDE 对齐）

使用方式：
  cd Genesis/rag_demo
  python indexers/indexer_knowledge_units.py
"""

import json
import os

# ====== 路径配置 ======
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(_THIS_DIR)                                         # rag_demo/
_KB_DIR   = os.path.join(_BASE_DIR, "knowledge_base")                          # rag_demo/knowledge_base/
RAG_DIR   = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", "phys_agent", "RAG"))  # phys_agent/RAG/

# 输入：从本地 knowledge_base/ 读取
CODE_INDEX_FILE   = os.path.join(_KB_DIR, "genesis_code_index.json")
API_KB_FILE       = os.path.join(_KB_DIR, "genesis_api_index.json")
# 输出：同时写入 phys_agent/RAG/（供 agent 直接使用）和本地 knowledge_base/（备份）
OUTPUT_FILE       = os.path.join(RAG_DIR, "genesis_knowledge_units.json")
LOCAL_OUTPUT_FILE = os.path.join(_KB_DIR,  "genesis_knowledge_units.json")

# embedding_text 中代码预览的最大字符数（保持代码风格，但控制长度）
CODE_PREVIEW_CHARS = 1200
# metadata 中 api_summaries 的最大字符数（Chroma metadata 值有大小限制）
API_SUMMARIES_MAX_CHARS = 2000
# metadata 中 code_preview 的最大字符数
CODE_META_PREVIEW_CHARS = 600


def build_api_lookup(api_kb: list) -> dict:
    """把 API 知识库列表转换为 {api_id: entry} 字典，方便 O(1) 查询。"""
    return {entry["api_id"]: entry for entry in api_kb if entry.get("api_id")}


def _strip_import_lines(code: str) -> str:
    """跳过开头的 import / from ... import ... 空行，返回剩余代码体。"""
    lines = code.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            i += 1
            continue
        if stripped == "":
            if i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if nxt.startswith("import ") or nxt.startswith("from "):
                    i += 1
                    continue
        break
    return "".join(lines[i:])


def build_unit(code_entry: dict, api_lookup: dict) -> dict:
    """
    把单个代码范例条目聚合为知识单元。

    :param code_entry: genesis_code_index.json 中的一条记录
    :param api_lookup: {api_id: api_entry} 字典
    :return: 知识单元 dict
    """
    meta = code_entry.get("metadata", {})
    file_id   = code_entry.get("id", "unknown.py")
    unit_id   = file_id.replace(".py", "")
    title     = meta.get("title", file_id)
    desc      = meta.get("desc", "")
    tags      = meta.get("tags", [])
    all_apis  = meta.get("all_apis", [])   # 全量 API（含 core）
    key_apis  = meta.get("key_apis", [])   # 关键 API（去 core）
    if not all_apis:
        # 兼容旧版 code_index（仅有 key_apis）
        all_apis = key_apis
    code      = code_entry.get("code", "")

    # --- 关联 API 文档（精简摘要） ---
    api_docs = []
    for api_id in all_apis:
        entry = api_lookup.get(api_id)
        if not entry:
            continue
        sig = entry.get("signature", "")
        summary = entry.get("summary", "")
        # 只取前 2 个参数描述，避免太长
        params = entry.get("parameters", [])[:2]
        param_str = ", ".join(
            f"{p['name']}: {p.get('desc', '')[:60]}"
            for p in params
            if isinstance(p, dict)
        )
        api_docs.append({
            "api_id":    api_id,
            "signature": sig,
            "summary":   summary[:200],
            "params_preview": param_str,
        })

    # --- 构建 embedding_text（代码风格，专为 HyDE 对齐设计）---
    # 格式：注释式 header（自然语言信息）+ 真实代码预览（embedding 向量对齐核心）
    api_names_str = ", ".join(key_apis) if key_apis else "none"
    tags_str = ", ".join(tags) if tags else "general"
    code_body = _strip_import_lines(code)
    code_preview = code_body[:CODE_PREVIEW_CHARS]

    embedding_text = (
        f"# Task: {title}\n"
        f"# Description: {desc}\n"
        f"# Domain: {tags_str}\n"
        f"# Genesis APIs used: {api_names_str}\n\n"
        f"{code_preview}"
    )

    # --- 构建 rerank_text（精简版，供 cross-encoder reranking）---
    rerank_text = f"{title} | Domain: {tags_str} | {desc}"
    key_apis_str_r = ", ".join(key_apis[:5]) if key_apis else ""
    if key_apis_str_r:
        rerank_text += f" | Key APIs: {key_apis_str_r}"

    return {
        "unit_id":       unit_id,
        "title":         title,
        "desc":          desc,
        "tags":          tags,
        "all_apis":      all_apis,
        "key_apis":      key_apis,
        "api_docs":      api_docs,
        "code":          code,
        "embedding_text": embedding_text,
        "rerank_text":   rerank_text,
    }


def build_knowledge_units():
    # --- 加载输入文件 ---
    if not os.path.exists(CODE_INDEX_FILE):
        print(f"❌ 找不到代码范例库: {CODE_INDEX_FILE}")
        return
    if not os.path.exists(API_KB_FILE):
        print(f"❌ 找不到 API 知识库: {API_KB_FILE}")
        return

    with open(CODE_INDEX_FILE, "r", encoding="utf-8") as f:
        code_index = json.load(f)
    with open(API_KB_FILE, "r", encoding="utf-8") as f:
        api_kb = json.load(f)

    print(f"📦 代码范例: {len(code_index)} 条")
    print(f"📚 API 知识库: {len(api_kb)} 条")

    api_lookup = build_api_lookup(api_kb)

    # --- 构建知识单元 ---
    units = []
    missing_apis_total = 0
    missing_apis_set = set()
    for entry in code_index:
        unit = build_unit(entry, api_lookup)
        # 统计有多少 all_api 在 API KB 里找不到（用于质量评估）
        all_apis = entry.get("metadata", {}).get("all_apis", []) or entry.get("metadata", {}).get("key_apis", [])
        missing = [k for k in all_apis if k not in api_lookup]
        if missing:
            missing_apis_total += len(missing)
            missing_apis_set.update(missing)
        units.append(unit)

    # --- 保存（写入 phys_agent/RAG/ 供 agent 使用，同时备份到本地 knowledge_base/）---
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(units, f, indent=2, ensure_ascii=False)
    os.makedirs(_KB_DIR, exist_ok=True)
    with open(LOCAL_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(units, f, indent=2, ensure_ascii=False)

    # --- 统计报告 ---
    total_api_links = sum(len(u["api_docs"]) for u in units)
    units_with_api = sum(1 for u in units if u["api_docs"])
    print(f"\n✅ 知识单元构建完成！")
    print(f"   总单元数:           {len(units)}")
    print(f"   有 API 文档关联的:  {units_with_api} / {len(units)}")
    print(f"   总 API 文档链接数:  {total_api_links}")
    print(f"   未找到的 all_apis:  {missing_apis_total}（可能是 AST 提取的 gs.alias，已忽略）")
    if missing_apis_set:
        missing_sorted = sorted(missing_apis_set)
        MAX_SHOW = 30
        shown = missing_sorted[:MAX_SHOW]
        print(f"   未找到的 all_apis 列表（去重后 {len(missing_sorted)} 个，最多显示 {MAX_SHOW} 个）:")
        for k in shown:
            print(f"     - {k}")
        if len(missing_sorted) > MAX_SHOW:
            print(f"     ... 还有 {len(missing_sorted) - MAX_SHOW} 个未显示")
    print(f"   输出文件 (agent):   {OUTPUT_FILE}")
    print(f"   输出文件 (local):   {LOCAL_OUTPUT_FILE}")

    if units:
        sample = units[0]
        print(f"\n🔎 样例预览（{sample['unit_id']}）:")
        print(f"   title:    {sample['title']}")
        print(f"   all_apis: {sample.get('all_apis', [])}")
        print(f"   key_apis: {sample['key_apis']}")
        print(f"   api_docs: {len(sample['api_docs'])} 条")
        print(f"   embedding_text 前 200 chars:")
        print("   " + sample["embedding_text"][:200].replace("\n", "\n   "))


if __name__ == "__main__":
    build_knowledge_units()

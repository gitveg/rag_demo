"""
loop_b/judge.py — 回路 B：错误信息收集（无 LLM，供人工审核）。

不再调用 LLM Judge（成本过高）。analyze_error() 改为收集原始错误上下文，
输出到 pending_review.md 供人工在网页端 Judge 分析 bad_pattern / correction / explanation。

如需 LLM 自动分析，使用 legacy/ 下的旧版脚本。
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG_DEMO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, RAG_DEMO_ROOT)

KB_DIR = os.path.join(RAG_DEMO_ROOT, "knowledge_base")
MEMORY_FILE = os.path.join(KB_DIR, "genesis_error_memory.json")
MAX_ERROR_LOG_CHARS = 8000


def analyze_error(code_path, error_log, file_id=None):
    """
    收集错误上下文供人工审核（不调用 LLM）。

    Args:
        code_path: 出错代码文件的路径
        error_log: 错误日志文本
        file_id: 记录 ID

    Returns:
        dict with keys: id, code, error_log, query_context
        —— 供 pending_review.md 使用，由人工补充 bad_pattern/correction/explanation
    """
    if file_id is None:
        file_id = os.path.basename(code_path)

    code_content = ""
    try:
        if code_path and os.path.exists(code_path):
            with open(code_path, "r", encoding="utf-8") as f:
                code_content = f.read()
    except Exception:
        pass

    # 提取文件头部的 User Query（gen 阶段写入的注释）
    query_context = "Unknown Context"
    for line in code_content.split("\n")[:5]:
        if "User Query:" in line:
            query_context = line.strip()
            break

    # 截断过长错误日志
    error_excerpt = (error_log or "")[:MAX_ERROR_LOG_CHARS]

    return {
        "id": file_id,
        "code": code_content[:2000],
        "error_log": error_excerpt,
        "query_context": query_context,
        # 以下字段由人工审核后填充：
        "bad_pattern": "",
        "correction": "",
        "explanation": "",
        "tags": [],
    }

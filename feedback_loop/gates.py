"""
gates.py — 执行闭环三条回路的人工审核门控。

不再使用 LLM Judge（成本过高），改为 fail-closed 策略：
  - review() 一律返回 {"pass": False, "pending": True}，即所有候选默认拒绝
  - 候选汇总到 pending_review.md 供人工在网页端 Judge 审核
  - 审核通过后由 processor.py --approve 执行实际入库

用法：
    from gates import LoopAGate, LoopBGate, LoopCGate

    gate = LoopAGate()
    result = gate.review(code, api_list, query)
    # result = {"pass": False, "pending": True, "reason": "Pending human review"}
    # 用 gate.format_for_review(...) 生成待审 markdown
"""

from __future__ import annotations

from typing import List, Optional


# ==================== 回路 A 门控：知识单元合格性审查 ====================

class LoopAGate:
    """
    判断执行成功的代码是否值得沉淀为新知识单元。

    启发式预过滤条件（在调用此 gate 之前检查）：
      - scene_build_started = True
      - API 数量 >= 3，代码行数 >= 20
      - Jaccard 去重通过（与现有单元相似度 < 0.8）

    预过滤通过后进入人工审核（pending_review.md）。
    """

    REVIEW_DIMS = [
        ("完整性", "是否包含完整的仿真流程（init → Scene → entities → build → step loop）？"),
        ("API 覆盖价值", "是否使用了不常见或有代表性的 API 组合？"),
        ("代码质量", "结构是否清晰、是否遵循 Genesis 惯例？"),
        ("新颖性", "与常见基础示例相比，是否有独特价值？"),
        ("可复用性", "其他用户能否参考这个代码模式？"),
    ]

    def __init__(self):
        pass  # 无 LLM 客户端

    def review(self, code: str, api_list: list, query: str) -> dict:
        """
        fail-closed：一律返回 pending，由人工审核。

        Returns:
            {"pass": False, "pending": True, "reason": "Pending human review"}
        """
        return {"pass": False, "pending": True, "reason": "Pending human review"}

    @staticmethod
    def format_for_review(
        index: int,
        source_id: str,
        query: str,
        all_apis: List[str],
        title: str,
        desc: str,
        tags: List[str],
        code: str,
        code_max_lines: int = 40,
    ) -> str:
        """生成单个回路 A 候选的 markdown 审查区块。"""
        code_lines = code.splitlines()
        code_preview = "\n".join(code_lines[:code_max_lines])
        if len(code_lines) > code_max_lines:
            code_preview += f"\n# ... (truncated, {len(code_lines)} lines total)"

        dims_md = "\n".join(
            f"- [ ] **{name}**: {desc}" for name, desc in LoopAGate.REVIEW_DIMS
        )

        return f"""### A-{index}: {title}

- **ID**: `{source_id}`
- **User Query**: {query}
- **APIs used** ({len(all_apis)}): {", ".join(all_apis[:15])}
- **Title**: {title}
- **Description**: {desc}
- **Tags**: {", ".join(tags) if tags else "(none)"}

**Code** (first {code_max_lines} lines):
```python
{code_preview}
```

**Review checklist**:
{dims_md}

**Decision**: [ ] Approve  /  [ ] Reject
**Notes**: ___
"""


# ==================== 回路 B 门控：错误记忆价值审查 ====================

class LoopBGate:
    """
    判断失败代码产生的错误模式是否值得作为错误记忆存入知识库。

    预过滤条件：
      - 排除 ModuleNotFoundError / TimeoutError / 纯语法错误
      - error_log < 8000 chars

    预过滤通过后进入人工审核（pending_review.md），
    由人工识别 bad_pattern / correction / explanation。
    """

    REVIEW_DIMS = [
        ("API 相关性", "这个错误是否与 Genesis API 的具体使用方式有关？（而非通用 Python 错误）"),
        ("可重复性", "其他用户是否很可能犯同样的错误？"),
        ("教育价值", "了解这个错误模式能否显著帮助未来的代码生成？"),
    ]

    def __init__(self):
        pass

    def review(self, bad_pattern: str = "", correction: str = "",
               explanation: str = "", tags: list = None,
               error_excerpt: str = "") -> dict:
        """
        fail-closed：一律返回 pending，由人工审核。

        Returns:
            {"pass": False, "pending": True, "reason": "Pending human review"}
        """
        return {"pass": False, "pending": True, "reason": "Pending human review"}

    @staticmethod
    def format_for_review(
        index: int,
        record_id: str,
        query: str,
        error_log: str,
        code_path: str = "",
        error_log_max_chars: int = 1500,
    ) -> str:
        """生成单个回路 B 候选的 markdown 审查区块（含原始错误供人工分析）。"""
        error_excerpt = error_log[:error_log_max_chars]
        if len(error_log) > error_log_max_chars:
            error_excerpt += f"\n# ... (truncated, {len(error_log)} chars total)"

        dims_md = "\n".join(
            f"- [ ] **{name}**: {desc}" for name, desc in LoopBGate.REVIEW_DIMS
        )

        return f"""### B-{index}: {query[:60]}

- **ID**: `{record_id}`
- **User Query**: {query}
- **Code Path**: `{code_path}`

**Error Log** (first {error_log_max_chars} chars):
```
{error_excerpt}
```

**Human analysis required** — please identify:
- **Bad Pattern** (写出错误的 API 调用模式，如 `scene.add(Sphere(...))`):
- **Correction** (正确的写法，如 `scene.add_entity(gs.morphs.Sphere(...))`):
- **Explanation** (一句话解释为什么错误、为什么正确):

**Review checklist**:
{dims_md}

**Decision**: [ ] Approve  /  [ ] Reject
**Notes**: ___
"""


# ==================== 回路 C 门控：约束质量审查 ====================

class LoopCGate:
    """
    判断为 API 生成的约束是否准确且有价值。

    预过滤条件：
      - symbol 成功映射到已知 API ID
      - 启发式约束非空

    预过滤通过后进入人工审核（pending_review.md）。
    """

    REVIEW_DIMS = [
        ("准确性", "约束是否正确反映了 API 的真实限制？"),
        ("可操作性", "约束是否明确告诉代码生成者应该/不应该做什么？"),
        ("非冗余性", "这个约束是否提供了常见文档中没有的新信息？"),
    ]

    def __init__(self):
        pass

    def review(self, api_id: str, constraints: list,
               error_examples: list = None) -> dict:
        """
        fail-closed：一律返回 pending，由人工审核。

        Returns:
            {"pass": False, "pending": True, "reason": "Pending human review"}
        """
        return {"pass": False, "pending": True, "reason": "Pending human review"}

    @staticmethod
    def format_for_review(
        index: int,
        api_id: str,
        constraints: List[str],
        error_examples: List[str],
        event_count: int,
    ) -> str:
        """生成单个回路 C 候选的 markdown 审查区块。"""
        constraints_md = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(constraints))
        examples_md = "\n".join(f"  - {e}" for e in error_examples[:6])

        dims_md = "\n".join(
            f"- [ ] **{name}**: {desc}" for name, desc in LoopCGate.REVIEW_DIMS
        )

        return f"""### C-{index}: `{api_id}`

- **API**: `{api_id}`
- **Event count**: {event_count}

**Generated constraints**:
{constraints_md}

**Error evidence**:
{examples_md}

**Review checklist**:
{dims_md}

**Decision**: [ ] Approve  /  [ ] Reject
**Notes**: ___
"""

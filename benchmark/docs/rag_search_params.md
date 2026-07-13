# rag_demo RAG Search 接口参数说明

> 本文档描述 `GenesisRAG.search()` 统一检索接口的全部参数，
> 以及 benchmark 实验中的核心变量维度。

## 接口签名

```python
GenesisRAG.search(
    query: str,
    *,
    # 查询重写
    rewrite_mode: str = "hyde",
    # 检索路由
    hyde_route: str = "unit",
    # 检索数量
    n_units: int = 5,
    n_api: int = 6,
    n_code: int = 1,
    n_snippet: int = 3,
    n_error: int = 0,
    # Core API 注入
    include_core_api: bool = True,
    core_api_limit: int = 40,
    # 过滤
    tag_filter: str = None,
    # 基础设施（可在 search 时覆盖 __init__ 默认值）
    use_hybrid: bool = None,           # None = 使用 __init__ 默认值
    distance_threshold: float = None,   # None = 使用 __init__ 默认值（0.5）
    # 后处理（当前 rag_demo 未实现，保留参数）
    rerank: bool = False,
    rerank_top_n: int = None,
    rerank_oversample: float = 2.0,
) -> list[dict]
```

返回值：`list[dict]`，每项 `{"type": "api"|"unit"|"code"|"snippet"|"error", "content": str, "meta": dict}`。

---

## 路由逻辑

```
rewrite_mode == "hyde" AND hyde_route == "unit"  →  unit 路径（知识单元为主检索）
其他所有情况                                         →  fourway 路径（API + code + snippet + error）
```

| 路径 | 检索源 | Core API 注入 |
|---|---|---|
| **unit** | 知识单元 → Core API（去重）→ API 语义补充 → 错误记忆 | 跳过知识单元已覆盖的 API |
| **fourway** | Core API → API 语义检索 → 代码范例 → 代码片段 → 错误记忆 | 无条件全量注入 |

---

## 实验维度

### ① 查询重写（rewrite_mode）— 3 档

| 值 | 含义 | 检索路由 |
|---|---|---|
| `none` | 原始 query 直接检索 | 强制 fourway |
| `translate` | 翻译为英文技术描述后检索 | 强制 fourway |
| `hyde` | 翻译 + 生成伪代码骨架后检索 | 可选 unit 或 fourway |

### ② 检索路由（hyde_route）— 2 档

| 值 | 含义 | 生效条件 |
|---|---|---|
| `unit` | 知识单元为主检索路径 | 仅 `rewrite_mode="hyde"` 时生效 |
| `fourway` | API / code / snippet / error 四路检索 | `none` / `translate` 强制走此路径；`hyde` 时可选 |

**①+② 有效组合共 4 种：**

| 组合 | rewrite_mode | hyde_route | 实际路径 |
|---|---|---|---|
| A | `none` | — | fourway |
| B | `translate` | — | fourway |
| C | `hyde` | `unit` | unit |
| D | `hyde` | `fourway` | fourway |

### ③ 检索数量 — 5 个连续参数

| 参数 | 默认值 | 影响路径 | 含义 |
|---|---|---|---|
| `n_units` | 5 | unit | 知识单元召回条数 |
| `n_api` | 6 | 两条路径 | API 语义检索条数 |
| `n_code` | 1 | fourway | 代码范例条数 |
| `n_snippet` | 3 | fourway | 代码片段条数 |
| `n_error` | 0 | 两条路径 | 错误记忆条数（0 = 不查） |

### ④ Core API 注入 — 2 个参数

| 参数 | 默认值 | 含义 |
|---|---|---|
| `include_core_api` | `True` | 是否注入固定 Core API 文档 |
| `core_api_limit` | 40 | Core API 注入条数上限 |

unit 路径下 Core API 会与知识单元已覆盖的 API 去重；fourway 路径下无条件全量注入。

### ⑤ 后处理（当前 rag_demo 未实现，保留参数）

| 参数 | 默认值 | 含义 |
|---|---|---|
| `rerank` | `False` | 是否在向量召回后重排序 |
| `rerank_top_n` | `None` | rerank 后保留的语义条数 |
| `rerank_oversample` | `2.0` | 启用 rerank 时的超采样系数 |

### ⑥ 过滤

| 参数 | 默认值 | 含义 |
|---|---|---|
| `tag_filter` | `None` | 意图标签过滤（如 `rigid_body`、`soft_body`），需与意图分类配合 |

---

## ⑥ 基础设施（可在 search 时覆盖）

| 参数 | 默认值 | 含义 |
|---|---|---|
| `use_hybrid` | `None`（使用 `__init__` 默认 `True`） | Symbol Boost 混合检索（Dense + API 符号匹配重排）。传 `False` 可禁用 |
| `distance_threshold` | `None`（使用 `__init__` 默认 `0.5`） | 余弦距离过滤阈值，超过此值的结果丢弃。传 `1.0` 相当于不过滤 |

这两个参数通过 save/restore 模式实现：`search()` 调用时临时覆盖 `self._use_hybrid` 和 `self.DISTANCE_THRESHOLD`，调用结束后自动恢复，不影响直接调用 `search_knowledge_units()` 等方法的默认行为。

`__init__` 级别默认值：

| 初始化参数 | 默认值 | 含义 |
|---|---|---|
| `use_hybrid` | `True` | 全局 Symbol Boost 开关 |
| `DISTANCE_THRESHOLD` | `0.5` | 全局距离过滤阈值 |

---

## benchmark 实验矩阵（当前）

`run_benchmark_batch.py` 中的 COMMANDS：

| 编号 | rewrite_mode | hyde_route | 实际路径 | 说明 |
|---|---|---|---|---|
| ① | `none` | — | fourway | 四路 baseline |
| ② | `hyde` | `unit` | unit | HyDE + 知识单元（默认） |
| ③ | `hyde` | `fourway` | fourway | HyDE + 四路检索 |

---

## 参考：phys_agent 对应参数

rag_demo 的 `search()` 签名与 `phys_agent/core/rag_interface.py` 完全对齐，
phys_agent baseline（`rewrite_mode=none`）走 fourway 路径，RAG 召回率约 70.6%。

---

*文档更新时间：2026-06-10*

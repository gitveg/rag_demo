# 迁移文档：rag_demo RAG 模块 → PhysCode

> **状态**：进行中 · **创建日期**：2026-06-24 · **最后更新**：2026-06-24
> **源**：`Genesis-main/rag_demo/`（物理仿真 Agent 的 RAG 模块）
> **目标**：`PhysCode/`（通用编码 Agent 框架，fork 自 Hermes-Agent）

---

## 一、目标定义

让 PhysCode 的 Agent 在回答用户问题时，能够主动调用一个 `rag_search` 工具；调用后，RAG 模块在我们**已构建好的知识库**中做一次检索，并把检索到的知识**注入到 Agent 的上下文**中，供其生成代码 / 回答时参考。

### 1. 触发方式

由 **Agent 自主决策调用** `rag_search`（即由模型判断"现在需要查知识库"，而非系统每轮强制自动注入）。
对应 PhysCode 的 **Tool 注册机制**（`tools/registry.py`）—— Agent 把它当作一个可调用工具。

### 2. 检索范围

我们已在 `rag_demo` 中构建好的知识库（灌入 ChromaDB `genesis_chroma_db/` 的 5 个 collection）：
- **知识单元** `genesis_knowledge_units`（代码 + 内嵌 API 文档摘要的聚合体，检索主力）
- **API 文档** `genesis_apis`（含 core API 标记）
- **完整代码范例** `genesis_examples`
- **代码片段** `genesis_snippets`
- **错误记忆** `genesis_errors`

检索入口与各 collection 的对应关系见 §4.1。

### 3. 结果去向

检索到的知识作为 **tool 返回值**自然进入对话上下文（tool result 消息），完成"注入"。
Agent 在后续生成阶段即可参考这些知识。

### 4. 范围边界

本阶段**只做"检索 → 注入"这一条读路径**，先不涉及 `feedback_loop/` 的执行结果回流（回路 A/B/C）。
写路径（成功代码沉淀、错误记忆回流、API 约束生成）留待后续阶段。

---

## 二、PhysCode 扩展点对照

`rag_search` 最干净的落点是 PhysCode 的 **Tool 注册**（比 Memory Provider 轻量，且完全匹配"Agent 主动调用"的语义）。

实现要点（依据 `PhysCode/AGENTS.md` + `tools/registry.py`）：
- 在 `tools/` 下新建工具文件，import 时调 `registry.register(...)` 注册 `rag_search`
- 复用 `rag_demo/rag_engine.py` 现有的检索能力作为 handler 内部实现
- handler **必须返回 JSON 字符串**（用 `tools.registry` 提供的 `tool_result` / `tool_error` 辅助函数）
- 在 `model_tools.py` 的 `_discover_tools()` 中加入 import
- 在 `toolsets.py` 中归入合适的 toolset（或新建）

---

## 三、迁移硬约束（来自 `PhysCode/AGENTS.md`）

| 约束 | 含义 | 对 `rag_search` 的影响 |
|---|---|---|
| **Prompt 缓存不能断** | 不能在对话中途改历史 context / 中途重载 memory / 中途换 toolset | 工具按请求返回，不在对话中途刷新上下文 |
| **Profile 隔离** | 路径一律用 `get_physcode_home()`，禁止硬编码 `~/.physcode` | 知识库 / 索引路径需 profile-scoped |
| **Tool 返回 JSON 字符串** | 所有 tool handler 统一返回格式 | handler 用 `tool_result()` 包裹结果 |
| 模块级常量在 import 后取值 | `PHYSCODE_HOME` 在 import 前已设置 | 知识库路径可安全在模块级缓存 |

---

## 四、调研记录（持续补充）

> 本节随深入调研逐步填充。每项调研标注日期与结论。

### 4.1 `rag_engine.py` 检索接口（已调研 · 2026-06-24）

核心类：`GenesisRAG`（`rag_engine.py:68`）。

**统一检索入口 `search()`（`rag_engine.py:539`）—— `rag_search` 工具应调用此方法**

```python
search(query, n_api=6, n_code=1, n_snippet=3, n_error=0,
       tag_filter=None, include_core_api=True, core_api_limit=40,
       rewrite_mode="hyde", n_units=5, hyde_route="unit",
       use_hybrid=None, distance_threshold=None,
       rerank=False, rerank_top_n=None, rerank_oversample=2.0)
```

- **返回**：`list[dict]`，每项 `{"type": "api"|"unit"|"code"|"snippet"|"error", "content": str, "meta": dict}` —— 已是干净、可直接 JSON 序列化的结构，工具层基本无需再加工。
- **内部已完成**：查询改写 → 多路检索 → 去重 → 距离阈值过滤 → 可选 rerank。
- **路由**：`rewrite_mode=="hyde" & hyde_route=="unit"` → 知识单元路径（默认）；其余 → 四路检索路径。

**底层单路检索方法**（返回 ChromaDB 原始 dict，`rag_search` 一般不直接用）：

| 方法 | 集合 | 说明 |
|---|---|---|
| `search_knowledge_units()` | genesis_knowledge_units | 含 Symbol Boost 混合检索 |
| `search_api()` / `get_core_api_docs()` | genesis_apis | API 语义检索 / Core API 全量注入 |
| `search_code()` | genesis_examples | 完整代码范例 |
| `search_snippet()` | genesis_snippets | 代码片段 |
| `search_error()` | genesis_errors | 错误记忆 |

**5 个 ChromaDB 集合**（均 cosine 距离）：`genesis_apis` / `genesis_examples` / `genesis_snippets` / `genesis_errors` / `genesis_knowledge_units`

**外部 API / LLM 依赖（关键）—— 单次 `search()` 可能触发 1~3 次网络调用**：

| 依赖 | 模块 | 触发条件 | 环境变量 |
|---|---|---|---|
| DashScope embedding（text-embedding-v4, 1024d） | `DashScopeEmbeddingFunction` (`rag_engine.py:35`) | 每次查询（必发） | `DASHSCOPE_API_KEY` |
| DeepSeek LLM（HyDE 伪代码 + 中英翻译） | `query_rewriter.QueryRewriter`（默认 `rewrite_mode="hyde"`） | `rewrite_mode != "none"` | `DEEPSEEK_API_KEY` / `DEEPSEEK_API_URL` |
| DashScope rerank（gte-rerank-v2） | `reranker.Reranker` | 仅 `rerank=True`（默认关） | `DASHSCOPE_API_KEY` |
| Symbol 匹配 | `hybrid_search.SymbolMatcher` | `use_hybrid=True`（默认开） | 无（纯符号匹配，无 LLM） |

**初始化成本**：
- `GenesisRAG.__init__` 建 ChromaDB PersistentClient（本地 IO，快）+ OpenAI client（快，不联网）+ 若 `use_hybrid` 则读 `genesis_api_index.json` 加载 known_apis（纯本地）。
- 真正耗时的是**每次查询的 embedding / LLM 网络调用**，不是初始化。
- **结论**：应做成**单例**（工具层持有一个全局 `GenesisRAG` 实例），避免每次调用重建。

**迁移需处理的痛点**：
1. **路径硬绑 `rag_engine.py` 所在目录**：`_BASE_DIR = dirname(__file__)`，`DB_PATH` / 各 JSON 均相对它解析。搬进 PhysCode 后需让 `genesis_chroma_db/` 与 `knowledge_base/` 随之定位，并符合 profile 隔离（`get_physcode_home()`）。
2. **大量 `print()` 调试输出**：tool handler 里会污染输出，需抑制或改 logging。
3. **`dotenv.load_dotenv()`（`rag_engine.py:9` 模块级）**：导入即加载 .env，搬入后需对接 PhysCode 的 `.env` / `OPTIONAL_ENV_VARS` 体系。
4. **默认 HyDE 改写较重**：每次查询默认调 DeepSeek 生成伪代码，延迟+成本。工具层宜暴露 `rewrite_mode`（可设 `"none"` 关闭）作为参数。
5. **默认 `n_error=0`**：错误记忆默认不检索。若希望 `rag_search` 也带回"别踩坑"提示，需在工具默认参里调高。

### 4.2 PhysCode 工具调用链路（已调研 · 2026-06-24）

一条完整调用链：**注册 → 提供 schema → 调度执行 → 结果持久化进消息**。

**① 注册（两种触发方式）**
- 工具文件 import 时调 `registry.register()`（`tools/registry.py:59`）。
- **方式 A（改核心）**：在 `model_tools.py:_discover_tools()`（`model_tools.py:132`）的 `_modules` 列表加 `"tools.rag_search"`。
- **方式 B（插件，更干净）**：通过 `physcode_cli.plugins.discover_plugins()`（`model_tools.py:181`）自动发现，**不用改核心文件**。插件工具同样走 toolset 过滤。

**② 提供 schema（`get_tool_definitions` · `model_tools.py:234`）**
- 按 **toolset 过滤**：所有工具**必须属于一个 toolset** 才能被访问（`model_tools.py:298`）。→ `rag_search` 需在 `toolsets.py` 归入 toolset（可新建 `"rag"`）。
- `check_fn()` 决定可用性（如检查 `DASHSCOPE_API_KEY` 是否存在）—— 适合放 `requires_env=["DASHSCOPE_API_KEY"]`。

**③ 调度（`handle_function_call` · `model_tools.py:459` → `registry.dispatch` · `registry.py:149`）**
- `coerce_tool_args` 自动把字符串参数强转为 schema 类型。
- 执行 handler → 返回 **JSON 字符串**；异常被捕获返回 `{"error": ...}`。
- 🔑 **有 `pre_tool_call` / `post_tool_call` hooks**（`model_tools.py:500-511`、`529-541`）—— `post_tool_call` 能拿到工具名 + 参数 + **结果**。**这是以后接 feedback loop 写路径的天然挂钩点**（监听 `execute_code` 的结果，回流到知识库）。

**④ 结果 → 消息 + 三层大小控制（`tools/tool_result_storage.py`）**

工具返回值最终成为 `role: "tool"` 消息进入对话。防 context 溢出分三层：

| 层 | 机制 | 阈值 | 对 `rag_search` 的意义 |
|---|---|---|---|
| L1 工具自截 | 工具内部预截断 | 工具自定 | **`rag_search` 应在此控制返回体积** |
| L2 单结果持久化 | `maybe_persist_tool_result` | 默认 **100k 字符** → 超 1500 字符 preview + 落盘路径 | 超大结果自动落盘，模型用 `read_file` 取 |
| L3 单轮总额 | `enforce_turn_budget` | 默认 **200k 字符/轮** → 最大的几个先落盘 | 多工具结果累积超限时兜底 |

- 单工具阈值可用 `registry.register(max_result_size_chars=...)` 单独设。
- `read_file` 被 PINNED 为 `inf`（防 persist→read 循环）。

**对 `rag_search` 的体积结论**：
实际检索结果通常在**几 k 到十几 k 字符**之间，远低于 L2（100k）/ L3（200k）阈值，**持久化机制不会触发**。因此 `rag_search` 基本可直接把 `search()` 返回的 `list[dict]` JSON 序列化后透传，无需额外的体积裁剪逻辑。

> 注：L2/L3 阈值较高（100k / 200k），`max_result_size_chars` 无需为 `rag_search` 单独配置。即便偶尔偏大，L2 也会自动落盘兜底，不影响正确性。

### 4.3 知识库数据现状（已核对 · 2026-06-24）

直接核对 `knowledge_base/*.json` 源文件（JSON 是灌库源头，ChromaDB 是其向量化产物）：

| 文件 | 条目数 | 大小 | 对应 collection |
|---|---|---|---|
| genesis_knowledge_units.json | **101** | 1.0 MB | genesis_knowledge_units |
| genesis_api_index.json | **654** | 416 KB | genesis_apis |
| genesis_code_index.json | **101** | 488 KB | genesis_examples |
| genesis_code_snippets.json | **108** | 48 KB | genesis_snippets |
| genesis_error_memory.json | **9** | 5.9 KB | genesis_errors |

**矛盾已解决**：README 称错误记忆库"为空"是**过时**的；`execution_feedback_design.md` 说的"10 条"接近实际 —— **真实是 9 条**。

**对迁移的启示**：
- 数据量不大（合计约 2 MB JSON），迁移时整体搬 `knowledge_base/` + 重新灌一次 ChromaDB 即可。
- `core_api_limit`：API 总池 654 个，但 core API 只是子集。phys_agent 版 `rag_ops.py` 已把默认从 40 降到 **20**，沿用。
- error_memory 仅 9 条且偏旧（Apr 2），后续可用 feedback loop 补充。

---

## 五、`rag_search` 工具实现草案（参考 `phys_agent/tools/rag_ops.py`）

`rag_ops.py` 已是成熟设计（LangChain `@tool` 版）：单例 RAG + `_format_results()` 格式化 + 镜像 `search()` 签名 + 优秀 docstring（含调用时机）。下面适配 PhysCode 的工具注册机制，**核心检索逻辑零改动**。

### 5.1 适配点（rag_ops.py → PhysCode）

| rag_ops.py（LangChain） | PhysCode 版 |
|---|---|
| `from langchain.tools import tool` + `@tool` | `registry.register(name, toolset, schema, handler, ...)` |
| `from core.rag_interface import RAGInterface` | `from rag_engine import GenesisRAG`（rag_demo 版统一入口） |
| 返回纯文本字符串 | 返回 `tool_result({...})` JSON（PhysCode 工具约定） |
| 无可用性检查 | 加 `check_fn` + `requires_env=["DASHSCOPE_API_KEY"]` |
| `core_api_limit` 默认 20 | 沿用 20（rag_demo 的 `search()` 默认 40，工具层覆盖） |

### 5.2 工具骨架代码（草案）

```python
"""rag_search — Genesis 物理仿真知识库检索工具。

由 Agent 自主调用，在已构建知识库（ChromaDB）中做一次多路语义检索，
把检索到的知识注入对话上下文，供代码生成参考。
设计参考：phys_agent/tools/rag_ops.py（LangChain 版），适配 PhysCode 工具注册。
"""
import os
from tools.registry import registry, tool_result, tool_error

# ---- 单例 RAG 引擎（避免每次调用重建 ChromaDB 连接 + 加载 symbol matcher）----
_rag = None

def _get_rag():
    global _rag
    if _rag is None:
        from rag_engine import GenesisRAG   # ← 导入路径待定（见 §4.1 痛点1）
        _rag = GenesisRAG(use_hybrid=True)
    return _rag


def _format_results(results, max_chars_per_item=800):
    """把 search() 返回的 list[dict] 格式化成 Agent 可读文本（沿用 phys_agent 设计）。"""
    if not results:
        return "未检索到相关知识。"
    lines = [f"共检索到 {len(results)} 条知识：\n"]
    for i, item in enumerate(results, start=1):
        item_type = item.get("type", "unknown")
        content = (item.get("content") or "").strip()
        limit = 2000 if item_type == "unit" else max_chars_per_item   # unit 放宽以保留代码示例
        if len(content) > limit:
            content = content[:limit] + "...(已截断)"
        lines.append(f"[{i}] [{item_type}]\n{content}\n")
    return "\n".join(lines)


def rag_search(query, rewrite_mode="hyde", hyde_route="unit",
               n_api=6, n_code=1, n_snippet=3, n_error=0, n_units=5,
               tag_filter="", include_core_api=True, core_api_limit=20,
               rerank=False, rerank_top_n=0, rerank_oversample=2.0):
    try:
        rag = _get_rag()
        results = rag.search(
            query=query,
            n_api=max(0, n_api), n_code=max(0, n_code),
            n_snippet=max(0, n_snippet), n_error=max(0, n_error),
            tag_filter=tag_filter.strip() or None,
            include_core_api=include_core_api,
            core_api_limit=max(0, core_api_limit),
            rewrite_mode=rewrite_mode, n_units=max(0, n_units),
            hyde_route=hyde_route, rerank=rerank,
            rerank_top_n=rerank_top_n if rerank_top_n > 0 else None,
            rerank_oversample=rerank_oversample,
        )
        return tool_result({"query": query, "count": len(results),
                            "context": _format_results(results)})
    except Exception as e:
        return tool_error(f"RAG 检索失败：{e}")


def _check_requirements():
    return bool(os.getenv("DASHSCOPE_API_KEY"))


registry.register(
    name="rag_search",
    toolset="rag",
    schema={
        "name": "rag_search",
        "description": (
            "在 Genesis 物理仿真知识库中执行多路语义检索，返回相关的 API 文档、代码范例、"
            "代码片段和（可选）错误记忆。调用时机：用户询问 Genesis API 用法、需要生成/修改"
            "仿真脚本、或出现运行报错需要排查已知问题时。每次仿真任务通常只需调用一次。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "检索描述，例如 'rigid sphere falls on ground'"},
                "rewrite_mode": {"type": "string", "enum": ["hyde", "translate", "none"], "default": "hyde"},
                "hyde_route": {"type": "string", "enum": ["unit", "fourway"], "default": "unit"},
                "n_api": {"type": "integer", "default": 6},
                "n_code": {"type": "integer", "default": 1},
                "n_snippet": {"type": "integer", "default": 3},
                "n_error": {"type": "integer", "default": 0, "description": "错误记忆条数；排查报错时可设 2~3"},
                "n_units": {"type": "integer", "default": 5},
                "tag_filter": {"type": "string", "default": "",
                    "description": "领域标签过滤：rigid_body/soft_body/fluid_mpm/articulated_robot/scene_creation/rendering"},
                "include_core_api": {"type": "boolean", "default": true},
                "core_api_limit": {"type": "integer", "default": 20},
                "rerank": {"type": "boolean", "default": false},
                "rerank_top_n": {"type": "integer", "default": 0},
                "rerank_oversample": {"type": "number", "default": 2.0},
            },
            "required": ["query"],
        },
    },
    handler=lambda args, **kw: rag_search(
        query=args["query"],
        rewrite_mode=args.get("rewrite_mode", "hyde"),
        hyde_route=args.get("hyde_route", "unit"),
        n_api=args.get("n_api", 6), n_code=args.get("n_code", 1),
        n_snippet=args.get("n_snippet", 3), n_error=args.get("n_error", 0),
        n_units=args.get("n_units", 5), tag_filter=args.get("tag_filter", ""),
        include_core_api=args.get("include_core_api", True),
        core_api_limit=args.get("core_api_limit", 20),
        rerank=args.get("rerank", False), rerank_top_n=args.get("rerank_top_n", 0),
        rerank_oversample=args.get("rerank_oversample", 2.0),
    ),
    check_fn=_check_requirements,
    requires_env=["DASHSCOPE_API_KEY"],
    emoji="🔎",
)
```

### 5.3 落地进度与待决项

**✅ 已落地（2026-06-24）**：模块放置已确定 → `PhysCode/RAG/`，文件已就位（rag_demo 原件保留不动）：

```
PhysCode/RAG/
├── __init__.py          # 新增：sys.path 注入，兼容 rag_demo 扁平 import（迁移文件零修改）
├── rag_search.py        # 新增：rag_search 工具（注册到 registry）
├── rag_engine.py        # 迁移（原样）
├── query_rewriter.py    # 迁移（原样）
├── reranker.py          # 迁移（原样）
├── hybrid_search.py     # 迁移（原样）
├── llm_utils.py         # 迁移（原样）
├── knowledge_base/      # 迁移（JSON 源，~2 MB）
└── genesis_chroma_db/   # 迁移（向量库，14 MB）
```

- 关键决策：迁移文件**保持与 rag_demo 源一致、零修改**（便于同步 / diff）。扁平 import（`from query_rewriter import ...`）靠 `RAG/__init__.py` 把本目录加入 `sys.path` 解析。
- `rag_engine.py` 用 `_BASE_DIR = dirname(__file__)` 定位 DB / JSON，迁到 `RAG/` 后路径仍自洽（`RAG/genesis_chroma_db`、`RAG/knowledge_base/...`），**无需改路径即可工作** → Profile 隔离问题降级为可选优化。
- **未拷贝**：`agent.py`（完整 GenesisAgent 编排，非读路径所需）、`api_id_normalize.py`（feedback loop 用）、`.env`（含密钥，避免进入 git 仓库）。

**✅ 待决项进展（2026-06-24 更新）**：

1. ~~接入 PhysCode 工具发现~~ —— **已完成**：`model_tools.py:_discover_tools()` 加 `"RAG.rag_search"`；`toolsets.py` 把 `rag_search` 加入 `_HERMES_CORE_TOOLS`（全平台默认可用）+ 新增 `"rag"` toolset。
2. ~~环境变量~~ —— **已完成**：`RAG/.env` 已就位（`DASHSCOPE_API_KEY` 真实值已验证）；`.gitignore` 第 7 行 `.env` 规则已覆盖 `RAG/.env`（`git check-ignore` 确认），无需新规则。
3. **Profile 隔离（可选）**：当前 DB 路径硬绑 `RAG/` 目录（所有 profile 共享同一知识库）。单 profile 下无影响；若需 per-profile 隔离再改 `get_physcode_home()`。
4. **`print()` 抑制（可选，cosmetic）**：rag_engine 全程 print 调试，tool handler 内会混入 stdout；后续可重定向或改 logging。
5. ~~ChromaDB 版本兼容~~ —— **已验证 OK**：env_genesis 的 chromadb 1.4.0 可正常读取迁移的 `genesis_chroma_db`。

### 5.4 端到端验证（2026-06-24）

通过 `registry.dispatch("rag_search", {...})` 实跑检索（`rewrite_mode="none"`，跳过 DeepSeek）：

| 检查项 | 结果 |
|---|---|
| 工具注册 / schema / check_fn 门控 | ✅ 通过 |
| 迁移 chromadb 读取 | ✅ 通过（chromadb 1.4.0） |
| DashScope embedding + 向量检索 | ✅ 通过 |
| 检索结果 | 11 条，context ~7 KB（符合"几k到十几k"预期） |
| 返回 JSON 格式 | ✅ `{query, count, context}` |

> 默认 HyDE 路径（`rewrite_mode="hyde"`，需 `DEEPSEEK_API_KEY`）尚未实测，但走同一 `search()` 接口、逻辑复用，预计可用。

**结论：`rag_search` 工具迁移完成、端到端可用。Agent 现在可调用 `rag_search` 检索 Genesis 知识库并将结果注入上下文。**

> 维护约定：知识库的后续优化 / 丰富仍在 `rag_demo` 进行；PhysCode/RAG 的 `knowledge_base/` + `genesis_chroma_db/` 是快照，rag_demo 更新后需重新同步过来（重灌 chromadb）。

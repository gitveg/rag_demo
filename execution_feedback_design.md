# 执行闭环反馈系统设计方案

> **项目**：Genesis 物理仿真 Agent — RAG 模块
> **日期**：2026-06-04
> **目标**：将代码执行结果（成功/失败）回流到知识库，实现三条自增长闭环

---

## 一、现状与动机

### 1.1 当前问题

系统已经具备完整的"检索→生成→执行"能力，但执行结果仅存在于内存中的 `SharedContext`，任务结束后即丢失。知识库是静态的：

| 数据 | 数量 | 状态 |
|---|---|---|
| 知识单元 | 101 条 | 静态，依赖手动索引器构建 |
| 错误记忆 | 10 条（knowledge_base/） | `genesis_errors` ChromaDB collection 已建已有数据 |
| API 约束 | 18 个 API（stage1） | 已有 `api_constraint_stage1.json`，但未注入 runtime API 文档 |
| 执行结果 | 每次运行产生 | 仅在 `output.log` 中以文本记录，无结构化利用 |

**核心浪费**：系统拥有 99% 的 RAG 系统都没有的东西——能真正执行代码并拿到 ground-truth 的成功/失败信号。但这个信号从未回流到知识库。

### 1.2 已有基础设施

系统已经搭好了所有"管道"，只差接通最后一步：

```
┌─────────────────────────────────────────────────────────────────┐
│  已有但未连通的基础设施                                          │
├─────────────────────────────────────────────────────────────────┤
│  ✅ genesis_errors ChromaDB collection（已创建，空）             │
│  ✅ search_error() 方法（已实现，查空库）                        │
│  ✅ mem_builder/ 3 阶段 pipeline（gen→execute→judge，离线可用）  │
│  ✅ build_api_constraint.py（symbol mapping + constraint gen）   │
│  ✅ indexer_code.py（AST 分析 + LLM 丰富）                      │
│  ✅ api_id_normalize.py（API ID 标准化映射）                     │
│  ✅ CodeRunner（结构化执行结果：success/stderr/execution_analysis）│
│  ✅ Critic（动态 RAG 二次检索 + 错误诊断）                       │
│  ❌ ingest_errors() 方法（不存在）                               │
│  ❌ 执行结果写回知识库的任何代码（不存在）                        │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 目标

设计统一的执行闭环反馈系统，连通三条回路：

```
              ┌──────────┐
              │ 代码执行  │
              │ (Runner) │
              └────┬─────┘
                   │
            ┌──────┴──────┐
            │             │
         成功 ✅        失败 ❌
            │             │
     ┌──────┴──────┐  ┌──┴──────────────┐
     │ 回路 A       │  │                 │
     │ 成功代码     │  ├─→ 回路 B: 错误记忆│
     │ → 新知识单元 │  ├─→ 回路 C: API 约束│
     └──────────────┘  └─────────────────┘
```

---

## 二、系统架构

### 2.1 整体分层

```
┌───────────────────────────────────────────────────────────────┐
│                    Runtime 层（rag_demo/mem_builder）          │
│                                                               │
│  run_and_collect.py                                           │
│    ├── GenesisAgent.solve() → 生成代码                        │
│    ├── execute_code()        → 执行代码                       │
│    └── write_execution_log() → 收集结果                       │
│                    │                                           │
│                    ▼                                           │
│           execution_log.jsonl  （结构化执行日志）               │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│              Processing 层（rag_demo/mem_builder）             │
│                                                               │
│  execution_feedback_processor.py  （统一处理器）               │
│       │                                                       │
│       ├── 回路 A: 成功代码 → 新知识单元                        │
│       │     复用: indexer_code.py (AST), indexer_ku.py (构建)  │
│       │                                                       │
│       ├── 回路 B: 失败代码 → 错误记忆                          │
│       │     复用: build_mem_judge.py (LLM judge)              │
│       │                                                       │
│       └── 回路 C: 失败代码 → API 约束                          │
│             复用: build_api_constraint.py (mapping + gen)      │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│               Storage 层（JSON + ChromaDB）                    │
│                                                               │
│  genesis_knowledge_units.json  →  ChromaDB knowledge_units    │
│  genesis_error_memory.json     →  ChromaDB genesis_errors     │
│  api_constraint.json           →  ChromaDB genesis_apis       │
│                                                               │
│  [新增] rag_interface.ingest_errors()                         │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 设计原则

1. **非侵入式**：收集 hook 不影响主流程，写入失败不报错
2. **离线处理**：反馈处理是离线批处理，不在 runtime 路径上增加延迟
3. **复用优先**：充分利用 mem_builder/ 和 indexers/ 已有的分析能力
4. **质量控制**：去重 + 过滤，避免低质量数据污染知识库

---

## 三、数据收集层（Runtime）

### 3.1 执行日志格式

在 Orchestrator 的执行循环末尾，将每次执行结果追加到 `workspace/logs/execution_log.jsonl`。

每条记录格式：

```json
{
  "timestamp": "2026-06-04T15:30:45",
  "query": "模拟一个红色刚体球从高处落到地面",
  "code_path": "workspace/static_coder_20260604_153045.py",
  "attempt": 2,
  "success": false,
  "error_type": "RuntimeError",
  "stderr": "Traceback (most recent call last):\n  ...",
  "execution_analysis": {
    "returncode": 1,
    "scene_created": true,
    "scene_build_started": false,
    "traceback_detected": true,
    "genesis_error_detected": true,
    "concise_error": "GenesisException: ...",
    "phase_summary": ["scene_created"]
  },
  "rag_knowledge_ids": ["unit_042", "api_Rigid", "api_Sphere"]
}
```

### 3.2 生成→执行→收集

通过 `run_and_collect.py` 脚本实现完整的闭环：

```
prompts (JSON) → GenesisAgent.solve() → 代码 → execute_code() → 结果 → execution_log.jsonl
```

该脚本在 `rag_demo/mem_builder/` 下，整合了 agent 调用、代码执行和结果收集三个步骤。

### 3.3 收集时机

每次执行（无论成功/失败）都记录。对于多轮重试：
- 成功的最后一轮：进入回路 A
- 每轮失败：进入回路 B 和 C
- 最后一轮仍失败：只记录失败，不进入回路 A

---

## 四、离线处理层

### 4.1 统一处理器

新建脚本：`Genesis-main/rag_demo/mem_builder/execution_feedback_processor.py`

```
用法：
    python execution_feedback_processor.py --log /path/to/execution_log.jsonl
    python execution_feedback_processor.py --log /path/to/execution_log.jsonl --loop-a-only
    python execution_feedback_processor.py --log /path/to/execution_log.jsonl --dry-run
```

处理流程：

```
读取 execution_log.jsonl
    │
    ├─ 分离成功/失败记录
    │
    ├─ 成功记录 → 回路 A（成功代码 → 知识单元）
    │   ├─ 读取代码文件
    │   ├─ AST 分析提取 API
    │   ├─ LLM 生成 title/desc/tags
    │   ├─ 关联 API 文档摘要
    │   ├─ 构建 embedding_text + rerank_text
    │   ├─ 去重检查
    │   └─ 追加到 genesis_knowledge_units.json
    │
    └─ 失败记录 → 回路 B + C
        │
        ├─ 回路 B（错误记忆）
        │   ├─ 结构化错误信息
        │   ├─ LLM judge → bad_pattern/correction/explanation
        │   ├─ 按 bad_pattern 去重
        │   └─ 追加到 genesis_error_memory.json
        │
        └─ 回路 C（API 约束）
            ├─ 从 traceback 提取 API 符号
            ├─ 映射到标准 API ID
            ├─ 生成约束描述
            ├─ 按 api_id 聚合去重
            └─ 更新 api_constraint.json
```

### 4.2 处理进度追踪

维护一个 `execution_feedback_progress.json` 文件，记录已处理的日志条目偏移量，避免重复处理：

```json
{
  "last_processed_offset": 150,
  "processed_files": ["execution_log_20260604.jsonl"],
  "last_run": "2026-06-04T16:00:00",
  "stats": {
    "loop_a_new_units": 3,
    "loop_b_new_errors": 12,
    "loop_c_new_constraints": 5
  }
}
```

---

## 五、三条反馈回路详细设计

### 5.1 回路 A：成功代码 → 新知识单元

**目标**：将执行成功的代码沉淀为新的知识单元，扩展知识库覆盖面。

**输入**：执行成功的代码文件 + 原始 query + execution_analysis

**处理步骤**：

**Step A1：AST 分析提取 API**

复用 `indexers/indexer_code.py` 的 `GenesisImportVisitor`：

```python
from indexers.indexer_code import GenesisImportVisitor
import ast

def extract_apis_from_code(code: str, known_apis: set) -> tuple[list[str], list[str]]:
    """提取代码中使用的 API，返回 (all_apis, key_apis)"""
    tree = ast.parse(code)
    visitor = GenesisImportVisitor(known_apis)
    visitor.visit(tree)
    all_apis = sorted(visitor.found_apis)
    key_apis = [a for a in all_apis if not a.startswith("genesis.init")
                and not a.startswith("genesis.Scene.build")
                and not a.startswith("genesis.Scene.step")]
    return all_apis, key_apis
```

**Step A2：LLM 生成元数据**

复用 `indexer_code.py` 中已有的 LLM enrichment prompt，为代码生成 title、description、tags。

**Step A3：关联 API 文档摘要**

从 `genesis_api_index.json` 中查找代码使用的 API 的文档摘要，构建 `api_docs` 字段。

**Step A4：构建知识单元**

复用 `indexer_knowledge_units.py` 的 `build_unit()` 逻辑，生成 `embedding_text` 和 `rerank_text`。

**Step A5：去重**

与现有知识单元比较：
- 计算新单元与所有现有单元的 API 集合 Jaccard 相似度
- 若最高相似度 > 0.8，视为重复，跳过
- 同时检查代码的 MD5 哈希

**Step A6：写入**

追加到 `genesis_knowledge_units.json`（写入 `knowledge_base/`）。

**过滤条件**（避免低质量单元入库）：
- API 数量 ≥ 3（太简单的代码价值低）
- 代码长度 ≥ 20 行
- execution_analysis.phase_summary 包含 `scene_build_started`（确保真正跑通了构建阶段）

### 5.2 回路 B：失败代码 → 错误记忆

**目标**：从执行失败中提取错误模式，生成 bad_pattern / correction / explanation 三元组，存入错误记忆供未来检索。

**输入**：执行失败的代码 + stderr + 原始 query

**处理步骤**：

**Step B1：结构化错误信息**

从 execution_result 中提取：
- `concise_error`：从 stderr 提取的 traceback
- `error_type`：错误类型
- `phase_summary`：执行到了哪个阶段

**Step B2：LLM Judge**

复用 `mem_builder/build_mem_judge.py` 的 `analyze_error()` 函数。该函数已经实现了：
- LLM prompt：分析代码 + error_log，输出 bad_pattern / correction / explanation / tags
- 过滤 trivial error（syntax error, file not found）
- 重试机制（503 / rate limit）

```python
from mem_builder.build_mem_judge import analyze_error

analysis = analyze_error(code_path, error_log, file_id=record_id)
# 返回: {"bad_pattern": "...", "correction": "...", "explanation": "...", "tags": [...]}
```

**Step B3：去重**

- 按 `bad_pattern` 字符串哈希去重（与 `build_mem_judge.py` 的逻辑一致）
- 同一个 bad_pattern 不重复入库

**Step B4：写入**

追加到 `genesis_error_memory.json`（写入 `knowledge_base/`）。

**过滤条件**：
- 排除 `ModuleNotFoundError`（依赖问题，非 API 错误）
- 排除 `TimeoutError`（执行超时，非代码错误）
- error_log 长度 < 8000 chars（超长的 Taichi stack trace 无意义）
- LLM judge 返回非 NULL

### 5.3 回路 C：失败代码 → API 约束

**目标**：从失败中提取 API 使用约束（如"add_camera 必须在 build() 前调用"），注入 API 文档。

**输入**：执行失败的代码 + stderr + 原始 query

**处理步骤**：

**Step C1：符号提取**

从 traceback 中提取涉及到的 API 符号：

```python
import re

def extract_error_symbols(traceback_text: str) -> list[str]:
    """从 traceback 中提取 genesis API 符号"""
    patterns = [
        r'gs\.(\w+(?:\.\w+)*)\(',          # gs.xxx.yyy(
        r'genesis\.(\w+(?:\.\w+)*)\(',      # genesis.xxx.yyy(
        r'AttributeError.*?\'(\w+)\'',       # AttributeError
    ]
    symbols = set()
    for pat in patterns:
        symbols.update(re.findall(pat, traceback_text))
    return list(symbols)
```

**Step C2：API ID 映射**

复用 `api_id_normalize.py` 的 `resolve_api_to_known()` 将符号映射到标准 API ID。

**Step C3：约束生成**

优先使用启发式规则（零成本），LLM 辅助（高准确度）：

```python
def generate_constraint_heuristic(error_msg: str, api_id: str) -> str | None:
    """启发式规则生成约束"""
    if "unexpected keyword argument" in error_msg:
        arg = re.search(r"'(\w+)'", error_msg)
        return f"Parameter '{arg.group(1)}' is not accepted by {api_id}." if arg else None
    if "missing.*required.*argument" in error_msg:
        return f"{api_id} requires a positional argument that was not provided."
    if "already built" in error_msg:
        return f"{api_id} must be called before scene.build()."
    if "no attribute" in error_msg:
        attr = re.search(r"no attribute '(\w+)'", error_msg)
        return f"{api_id} has no attribute '{attr.group(1)}'." if attr else None
    return None
```

启发式无法覆盖时，调用 LLM judge（复用 `build_api_constraint.py` 的 `JudgeLLM` 类）生成约束。

**Step C4：聚合去重**

按 `api_id` 聚合约束：
- 每个约束计算文本哈希，相同约束不重复添加
- 每个 API 最多保留 6 条约束 + 6 条 error_examples

**Step C5：写入**

更新 `api_constraint.json`。格式与 `api_constraint_stage1.json` 一致：

```json
{
  "generated_at": "2026-06-04T16:00:00",
  "summary": {"api_count": N, "mapped_event_count": M},
  "apis": [
    {
      "api_id": "genesis.Scene.add_camera",
      "constraints": ["add_camera must be called before scene.build()"],
      "error_examples": ["Scene is already built."],
      "event_count": 3,
      "sources": ["s1_camera_medium_003", "runtime_20260604_001"]
    }
  ]
}
```

---

## 六、重新灌库层

### 6.1 灌库接口

`rag_engine.py` 的 `GenesisRAG` 已具备完整的灌库方法：
- `ingest_errors()` — 错误记忆灌库（已实现，line 254-291）
- `ingest_apis()` — API 文档灌库（已支持 constraints 字段）
- `ingest_knowledge_units()` — 知识单元灌库

### 6.2 API 约束注入

`ingest_apis()` 已支持 constraints 字段。反馈处理器会自动将新约束合并到 `api_constraint.json`，重新灌库时通过 `merge_constraints_to_api_index()` 合并到 API 索引中。

### 6.3 灌库流程

处理完成后，执行完整的重新灌库：

```bash
# 1. 处理 execution_log.jsonl
python mem_builder/execution_feedback_processor.py --log workspace/logs/execution_log.jsonl

# 2. 重新灌库（让新增的错误记忆、知识单元、API 约束生效）
python rag_engine.py
```

`rag_engine.py` 的 main 块已经会调用 `ingest_errors()` 和 `ingest_knowledge_units()`，新增的数据会自动被灌入 ChromaDB。

---

## 七、质量控制

### 7.1 去重策略

| 回路 | 去重键 | 策略 |
|---|---|---|
| A（知识单元） | 代码 MD5 + API 集合 Jaccard | MD5 完全相同跳过；Jaccard > 0.8 警告 |
| B（错误记忆） | `bad_pattern` 字符串哈希 | 完全相同跳过 |
| C（API 约束） | 约束文本哈希 + api_id | 同 API 下相同约束跳过 |

### 7.2 过滤门槛

| 回路 | 必须满足的条件 |
|---|---|
| A | API 数 ≥ 3，代码行数 ≥ 20，`scene_build_started` = True |
| B | 排除 ModuleNotFoundError / TimeoutError，error_log < 8000 chars，LLM 非 NULL |
| C | 成功映射到已知 API ID，约束非空 |

### 7.3 可选：人工审核

对于高风险场景（如生产环境），可以配置 `--dry-run` 模式：
- 处理器将结果写入 pending 文件（如 `pending_units.json`、`pending_errors.json`）
- 人工审核确认后，再执行正式入库
- 适合初期验证阶段，确认质量后可切换为自动模式

---

## 八、与现有系统的集成

### 8.1 文件清单

| 文件 | 类型 | 职责 |
|---|---|---|
| `feedback_loop/run_and_collect.py` | Runtime 层 | 生成→执行→收集，输出 execution_log.jsonl |
| `feedback_loop/processor.py` | 处理层 | 薄编排，调现有模块 + 审核门控 |
| `feedback_loop/gates.py` | 审核层 | 三条回路的 LLM 审核门控 |
| `feedback_loop/utils.py` | 工具层 | JSONL 读写、AST 分析、去重、单元构建 |
| `feedback_loop/build_mem_judge.py` | 已有 | 回路 B 核心：LLM judge 分析错误 |
| `feedback_loop/build_api_constraint.py` | 已有 | 回路 C 核心：错误解析→API 映射→约束生成 |
| `feedback_loop/agent.py` | 已有 | GenesisAgent，被 run_and_collect 调用 |
| `feedback_loop/query_rewriter.py` | 已有 | HyDE + 翻译改写 |

### 8.2 不涉及的改动

- 不修改 `agent.py`（GenesisAgent.solve() 接口不变）
- 不修改 `rag_engine.py`（已有 ingest_errors() 和 search_error()）
- 不修改任何 indexer
- 不修改 `build_mem_judge.py` / `build_api_constraint.py`（直接复用）

### 8.3 集成后数据流

```
benchmark/query.json (prompts)
    │
    ▼
run_and_collect.py
    ├── GenesisAgent.solve(query) ──→ 代码生成
    ├── execute_code()             ──→ 代码执行
    └── write_execution_log()      ──→ execution_log.jsonl
            │
            ▼
    [离线] execution_feedback_processor.py
            │
            ├── 成功 → genesis_knowledge_units.json
            ├── 失败 → genesis_error_memory.json
            └── 失败 → api_constraint.json
                    │
                    ▼
            python rag_engine.py → 重新灌库（ChromaDB）
                    │
                    ▼
            下次 Agent.solve() 时，新增知识已可被检索到
```

---

## 九、实施步骤

| 步骤 | 内容 | 文件 |
|---|---|---|
| **Step 1** | 创建共享工具函数 | `mem_builder/feedback_utils.py` |
| **Step 2** | 创建离线反馈处理器（三条回路） | `mem_builder/execution_feedback_processor.py` |
| **Step 3** | 创建生成→执行→收集脚本 | `mem_builder/run_and_collect.py` |
| **Step 4** | 运行并验证整条链路 | CLI 命令 |

完整运行命令：

```bash
cd rag_demo

# 1. 运行生成→执行→收集（用 benchmark 的 prompts）
python feedback_loop/run_and_collect.py --prompts benchmark/query.json --max-prompts 5

# 2. 离线处理反馈（三条回路 + LLM 审核门控）
python feedback_loop/processor.py --log workspace/logs/execution_log_*.jsonl

# 3. 重新灌库（让新增知识生效）
python rag_engine.py
```

---

## 十、验证方案

### 10.1 单元验证

```bash
# 验证生成→执行→收集（用 1 个 prompt 测试）
python mem_builder/run_and_collect.py --prompts benchmark/query.json --max-prompts 1
# 检查 workspace/logs/execution_log_*.jsonl 是否有记录

# 验证反馈处理器（试运行）
python mem_builder/execution_feedback_processor.py --log workspace/logs/execution_log_*.jsonl --dry-run

# 验证反馈处理器（正式）
python mem_builder/execution_feedback_processor.py --log workspace/logs/execution_log_*.jsonl --loop-b-only
```

### 10.2 集成验证

1. 运行 `run_and_collect.py` 跑 benchmark 的 prompts，生成执行日志
2. 运行 `execution_feedback_processor.py` 处理日志
3. 检查 `genesis_error_memory.json` 是否新增了错误条目
4. 运行 `python rag_engine.py` 重新灌库
5. 运行 agent，验证错误记忆能通过 `search_error()` 被检索到

### 10.3 质量验证

- 人工抽检新生成的错误记忆：bad_pattern 是否准确，correction 是否正确
- 人工抽检新生成的 API 约束：是否与 Genesis 实际行为一致
- 运行 benchmark 对比：错误记忆启用后，RAG Hit Rate 是否有变化

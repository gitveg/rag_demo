# Feedback Loop B/C 生产化完善与落地计划

> 日期：2026-07-13  
> 状态：实施方案，待按阶段落地  
> 范围：`rag_demo/feedback_loop`、`rag_engine.py`、`agent.py`、benchmark 与知识发布链路  
> 关联文档：[`feedback_loop_v2_design.md`](./feedback_loop_v2_design.md)

## 1. 执行摘要

Loop B/C 的目标不是“从每个失败中生成一条文本”，而是建立一条可信、可验证、可触发、可回滚的知识生产线：

```text
真实执行事实
  -> 唯一失败诊断
  -> 聚类与 B/C 路由
  -> 原子知识候选
  -> 确定性校验 / 修正重放
  -> 人工批准
  -> 版本化发布
  -> 精确触发
  -> 效果归因与淘汰
```

Loop B 与 Loop C 的产品边界如下：

- **Loop B / Error Memory**：面向“代码模式”的错误记忆，回答“这种写法为什么错，应该改成什么”。适合不存在的 API、跨 API 组合、对象类型误用、Tensor/NumPy 混用等问题。
- **Loop C / API Constraint**：面向“单个规范 API”的事实约束，回答“使用这个 API 时必须满足什么条件”。适合参数限制、生命周期、数值关系、对象类型和求解器兼容条件。
- **Discard / Run Health**：依赖、资源、Timeout、runner、本地资产偶发状态等运行健康问题，不进入生成知识。

本方案的核心设计决策：

1. **先诊断，后派生 B/C**：B/C 不再分别解析原始日志。
2. **存储丰富、投影简洁**：后台保存完整证据；Agent 只看到短小、原子、可执行的知识。
3. **结构化触发优先**：API ID、AST 模式和错误签名优先，向量相似度只做 fallback。
4. **知识必须可归因**：每条 B/C 都有稳定 ID，记录是否被展示、命中、采用以及后续结果。
5. **发布默认 fail-closed**：LLM 可以生成建议，不能单独批准或发布。
6. **先修可信执行，再扩产知识**：`online-full` 中的 runner 污染必须先解决，否则会从错误事实中学习。

## 2. 当前实验结论与问题基线

### 2.1 `online-full` 漏斗

当前 100 条执行记录的实际漏斗为：

| 阶段 | 数量 | 结论 |
|---|---:|---|
| 总记录 | 100 | 全量实验 |
| `process_passed` | 27 | 仅表示进程通过，不代表物理正确 |
| 失败记录 | 73 | 需要继续分类 |
| 当前规则判定 knowledge eligible | 68 | 排除 2 generation、2 timeout、1 dependency |
| 解析出的错误事件 | 70 | 两个记录含多个错误事件 |
| 映射到 API 的错误事件 | 25 | 覆盖 11 个 API |
| Loop C 候选 | 4 | 共 4 条约束 |
| Loop B 候选 | 68 | 当前是一 event 一候选，尚未聚类 |

Loop C 的主要损失不是发生在错误解析，而是发生在“已映射错误 -> 约束生成”：25 个已映射错误中，只有 4 个命中了当前固定模板。

### 2.2 新发现的 P0 runner 污染

68 个 B 候选中有 29 个循环导入失败：

- `partially initialized module 'genesis'`；
- `partially initialized module 'torch'`；
- `circular import`。

根因是执行产物统一命名为 `code.py`。Torch 导入 `pdb` 后，`pdb` 导入标准库 `code`，Python 却优先加载了任务目录中的生成脚本 `code.py`，造成脚本递归执行。

这 29 条约占当前 B 候选的 43%，应归类为 runner/infrastructure failure。当前 `online-full` 的整体通过率不能直接用于判断 RAG 效果。

### 2.3 当前 Loop B 的主要缺陷

1. 一条失败 event 生成一个候选，没有按错误签名、API 和代码模式聚类。
2. `bad_pattern/correction/explanation` 依赖人工逐条填写，68 条审核成本过高。
3. 现有错误记忆缺少 `api_ids/error_signature/ast_pattern/version/evidence` 等触发与审计字段。
4. 错误记忆主要用用户 query 做向量召回，用户需求与错误代码模式天然不相似。
5. 检索结果没有稳定携带 error memory ID，无法准确写入 `knowledge_ids`。
6. 没有记录知识是否与 draft 匹配、是否被采用、是否真正消除了同类错误。
7. 当前去重只比较规范化后的 `bad_pattern` 文本，无法识别语义相同但写法不同的模式。
8. 通用 Python 错误、引擎内部错误、API 误用之间的边界仍然粗糙。

### 2.4 当前 Loop C 的主要缺陷

1. 约束生成器只支持少量固定错误文案，无法处理生命周期、数值关系和兼容性条件。
2. API 映射主要依赖错误文本和 traceback 中直接出现的 `gs.*` / `scene.*`，变量方法和跨 API 关系容易丢失。
3. 一个候选可包含多条约束，不利于单条审核、冲突处理、版本更新和效用归因。
4. 当前约束多为“不要使用 X”，缺少正确替代方案或适用条件。
5. 已批准约束需要合并回静态 API index 并重建 Chroma，发布成本高且容易漂移。
6. 约束随 API 文档出现，但没有独立 constraint ID，无法知道具体哪条约束被展示或产生效果。
7. 只做精确字符串去重，没有规范化事实键、语义冲突和版本范围判断。
8. API index 中部分构造器只有 `**data`，单靠签名不能提供可靠字段信息，需要结合 Options/Pydantic 字段和源码 guard。

### 2.5 当前链路中被低估的高价值错误

`online-full` 中至少包含以下高置信、可泛化知识，但当前 C 没有产生对应约束：

- `Scene.start_recording()` 必须在 `scene.build()` 前调用：4 次；
- `Scene.add_force_field()` 必须在 `scene.build()` 前调用：2 次；
- SAPCoupler 需要 `precision="64"`：1 次；
- `Terrain.subterrain_size` 必须是 `horizontal_scale` 的整数倍：1 次；
- SAP coupling 下 primitive plane 不能作为用户指定碰撞几何：5 次；
- MPM 粒子必须位于 solver boundary 内：3 次。

合理目标不是把 68 个失败变成 68 条知识。按当前数据粗估，清理 runner 污染并聚类后，约 26 个非 runner 错误签名中应沉淀约 8–12 条高质量 C 约束和若干 B 错误记忆。

## 3. 第一性原则

### 3.1 闭环的最终目标

反馈闭环的成功标准不是候选数量，而是：

> 在不显著增加上下文、延迟和误导风险的前提下，未来任务中同类可避免错误的发生率持续下降。

一条生产知识必须同时满足：

1. **真实**：来源是完整、不可变、可定位的执行证据。
2. **相关**：根因确实与代码/API 用法有关，而不是环境噪音。
3. **可操作**：明确告诉 Agent 应避免什么、改成什么。
4. **可泛化**：不是某台机器、某个临时路径或单次随机状态。
5. **可触发**：未来能通过 API、AST 模式或错误签名找到它。
6. **简洁**：进入 prompt 的内容是原子规则，不是长篇事故报告。
7. **可验证**：修正后能通过静态检查、源码事实校验或重放。
8. **可归因**：知道它何时被展示、匹配和采用，以及结果如何。
9. **可撤销**：有状态、版本、来源和回滚路径。

### 3.2 后端复杂性与 Agent 简洁性分离

“不能太复杂”应约束 serving surface，而不是牺牲后端证据。

```text
后台存储：完整 traceback、代码、源码 guard、适用版本、重放、审核和效用
Agent 看到：1 条短约束，或 Avoid / Use / Why 三行错误记忆
```

这样既能保证工程可信度，又能控制 prompt 复杂度。

### 3.3 不追求一失败一知识

知识产出应经过三层压缩：

```text
失败 event
  -> 规范化 diagnosis
  -> 同根因 cluster
  -> 一条原子 B/C 知识
```

重复失败主要用于提高 `support_count` 和置信度，不应重复制造知识条目。

### 3.4 确定性事实优先于 LLM 判断

优先级为：

1. API 签名、Options 字段和源码显式 guard；
2. traceback 用户 frame + AST 代码位置；
3. 同环境 failing/corrected replay；
4. 多个独立任务重复出现；
5. LLM 诊断与文本压缩建议。

LLM 不应覆盖与源码、签名或重放冲突的结果。

## 4. Loop B/C 的职责边界

### 4.1 路由规则

| 情况 | 路由 | 示例 |
|---|---|---|
| 单个已知 API 的参数、生命周期或数值约束 | C | `Terrain.subterrain_size` 必须整除 `horizontal_scale` |
| 单个已知 API 不支持某参数，且可给出正确替代字段 | C | Lidar 使用 `pos_offset`，不是 `pos` |
| 不存在的 API、模块或方法，需要指向另一个 API | B | `gs.surfaces.Metallic` -> 使用受支持的 surface 类型 |
| 跨多个 API/对象的组合错误 | B | NumPy array 与 Torch Tensor 混算 |
| 条件兼容规则有明确主 API | C，带 related APIs | SAPCoupler 与 Plane collision 的兼容限制 |
| 条件兼容规则没有清晰主 API | B | 多对象、多阶段控制模式错误 |
| 依赖、OOM、Timeout、runner、驱动、临时资产状态 | Discard / Run Health | circular import、缺 DLL、显存不足 |
| 引擎内部 bug，用户无可靠修正 | Issue/Health，不进入 B/C | CUDA illegal address |

### 4.2 原子知识原则

- 一条 B 只描述一个坏模式和一个修正方向。
- 一条 C 只描述一个事实约束。
- 一个 API 可以拥有多条 C，但每条独立审核、版本化和统计。
- 一次 diagnosis 可以派生 B 或 C；只有确有不同消费价值时才允许同时派生，避免 B/C 重复表达同一事实。

### 4.3 典型路由示例

#### C：Terrain 数值约束

```text
Set each subterrain_size component to an integer multiple of horizontal_scale.
```

#### C：Scene 生命周期

```text
Call Scene.add_force_field(...) before scene.build(); the scene is immutable to this operation after build.
```

#### B：不存在的方法

```text
Avoid: drone.set_attitude(...)
Use: a supported control/state API exposed by the returned DroneEntity.
Why: DroneEntity does not define set_attitude.
```

#### Discard：runner 污染

```text
AttributeError: partially initialized module 'torch' ... circular import
```

它反映的是执行器文件命名问题，不应提醒未来 Agent 修改 Genesis 代码。

## 5. 目标架构

```text
Prompt / Benchmark Task
        |
        v
Generation + Retrieval Trace
        |
        v
Trusted Runner -------- immutable artifacts --------+
        |                                          |
        v                                          v
Outcome Classifier                         Attempt Store
        |
        v
Traceback Parser -> User Frame -> AST Inspector -> API Resolver
        |
        v
FailureDiagnosis
        |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
     Discard           Loop B Builder       Loop C Builder
                            |                   |
                            +--------+----------+
                                     v
                           Compactness / Quality Lint
                                     |
                                     v
                           Static / Source / Replay Verify
                                     |
                                     v
                              Human Review
                                     |
                                     v
                           Versioned Knowledge Snapshot
                                     |
                      +--------------+--------------+
                      |                             |
                      v                             v
              B Trigger Index                 C API Overlay
                      |                             |
                      +--------------+--------------+
                                     v
                         Agent Prompt + Draft Audit
                                     |
                                     v
                         Exposure / Adoption / Outcome
```

## 6. 核心数据契约

### 6.1 FailureDiagnosis

B/C 只能消费统一 diagnosis，不再各自解析执行日志。

```json
{
  "diagnosis_id": "diag_<hash>",
  "event_id": "evt_...",
  "category": "api_lifecycle",
  "root_cause": "Scene.add_force_field was called after scene.build",
  "primary_api_id": "genesis.Scene.add_force_field",
  "related_api_ids": ["genesis.Scene.build"],
  "error_signature": "GenesisException:scene_already_built",
  "user_frame": {
    "file": "generated_script.py",
    "line": 45,
    "source": "scene.add_force_field(wind)"
  },
  "ast_pattern": "Call(api=genesis.Scene.add_force_field, phase=post_build)",
  "evidence": [
    {"kind": "traceback", "artifact": "traceback.txt"},
    {"kind": "code", "artifact": "code.py", "line": 45},
    {"kind": "source_guard", "path": "genesis/utils/misc.py", "line": 136}
  ],
  "confidence": "high",
  "generalizable": true,
  "route": "C",
  "classifier_version": "diagnosis_v1"
}
```

### 6.2 Loop B ErrorMemory

Canonical record：

```json
{
  "memory_id": "err_<normalized_payload_hash>",
  "status": "approved",
  "trigger": {
    "api_ids": ["genesis.options.surfaces.Diffuse"],
    "bad_symbols": ["genesis.options.surfaces.Metallic"],
    "error_signatures": ["AttributeError:module_has_no_attribute:Metallic"],
    "ast_patterns": ["Call(symbol=gs.surfaces.Metallic)"],
    "tags": ["rendering", "namespace_error"]
  },
  "bad_pattern": "gs.surfaces.Metallic(...) ",
  "correction": "Use a surface class that exists in the current Genesis API, such as gs.surfaces.Diffuse(...).",
  "why": "The surfaces namespace does not expose Metallic in this Genesis version.",
  "scope": {
    "genesis_version_min": "0.3.8",
    "genesis_version_max": null
  },
  "evidence_ids": ["diag_..."],
  "support_count": 1,
  "verification": {
    "status": "source_verified",
    "failing_event_id": "evt_...",
    "corrected_event_id": null
  },
  "review": {
    "decision": "approved",
    "reviewer": "human",
    "notes": "..."
  }
}
```

### 6.3 Loop C ApiConstraint

Canonical record：

```json
{
  "constraint_id": "con_<normalized_fact_hash>",
  "api_id": "genesis.options.morphs.Terrain",
  "status": "approved",
  "rule_type": "numeric_relation",
  "rule": "Set each subterrain_size component to an integer multiple of horizontal_scale.",
  "applies_when": "Constructing Terrain with generated subterrain geometry.",
  "related_api_ids": [],
  "scope": {
    "genesis_version_min": "0.3.8",
    "genesis_version_max": null
  },
  "evidence_ids": ["diag_..."],
  "support_count": 1,
  "verification": {
    "status": "source_verified",
    "source_path": "genesis/options/morphs.py",
    "failing_event_id": "evt_...",
    "corrected_event_id": null
  },
  "priority": "high",
  "review": {
    "decision": "approved",
    "reviewer": "human"
  }
}
```

### 6.4 稳定 ID 与去重键

- `diagnosis_id`：由 event ID + 规范化 root cause + primary API 生成。
- `memory_id`：由规范化 AST pattern + correction + scope 生成。
- `constraint_id`：由 api_id + rule_type + 规范化事实内容 + scope 生成。
- 重复 event 只增加 evidence/support，不生成新知识 ID。
- 文本改写但事实相同，不应生成新约束；事实变化或版本 scope 变化才创建新版本。

## 7. 简洁性规范

### 7.1 B 的 serving 投影

Agent 侧只展示：

```text
Avoid: <bad pattern>
Use: <correction>
Why: <one short reason>
```

硬性限制：

- 一条 B 最多 3 行；
- rendered text 建议不超过 120 tokens；
- `bad_pattern` 必须能对应代码或 AST 模式；
- `correction` 必须是正向可执行动作；
- `why` 只解释直接根因，不复述完整 traceback；
- 首次生成最多展示 2 条 B，总预算建议不超过 240 tokens。

### 7.2 C 的 serving 投影

- 一条 C 是一个句子，建议不超过 60 tokens；
- 一条规则只包含一个约束；
- 优先采用“动作 + 条件”，而不是泛化提醒；
- 禁止使用“check docs”“verify API”“be careful”等不可执行表达；
- 每个 API 默认最多展示 3 条 active constraints；
- 全局 C overlay 设 token budget，按当前任务、API 命中和 utility 选择，不把全部历史约束塞入 prompt。

### 7.3 后台字段不直接进入 prompt

以下字段只用于审计、排序和验证：

- 完整 traceback；
- 原始 query；
- 所有 evidence；
- support event 列表；
- reviewer notes；
- 模型 prompt/response；
- 版本和发布历史；
- utility 统计。

## 8. 可信执行与失败诊断

### 8.1 P0：修复 runner

必须完成：

1. 生成脚本不再命名为 `code.py`，使用不易与标准库冲突的名称，如 `generated_attempt.py`。
2. runner 使用受控 import path；必要时通过隔离 wrapper 启动，防止 artifact 目录污染标准库解析。
3. benchmark、feedback loop 和已有代码重放共用同一个 runner。
4. runner 启动前执行 self-check：在相同执行配置下验证 `import code/pdb/torch/genesis` 的解析路径。
5. circular-import + 本地脚本 shadowing 归类为 `runner_infrastructure`。
6. runner/version 写入 environment fingerprint。
7. 对 `online-full` 受影响的 29 条记录标记 quarantine，不得进入 B/C。

建议先无模型重放现有 100 份生成代码，得到“同一代码、修复 runner 后”的可信执行基线，再决定是否进行新的全量在线生成。

### 8.2 Failure taxonomy

建议诊断类别：

```text
generation_infra
runner_infrastructure
dependency
resource
timeout
syntax
asset_path
python_logic
tensor_type
api_symbol
api_signature
api_lifecycle
api_compatibility
api_numeric_constraint
engine_internal
physics_semantic
unknown
```

默认路由：

- `api_*`：允许进入 B/C；
- `python_logic/tensor_type`：只允许进入 B；
- `asset_path`：默认进入 run health；只有存在稳定、可移植的 canonical asset 修正时才允许 B；
- `generation/runner/dependency/resource/timeout/engine_internal`：禁止进入 B/C；
- `unknown`：进入诊断待审，不直接生成知识。

### 8.3 Traceback 与 user frame

解析器需要：

1. 去除 ANSI、Genesis 重复 ERROR 行和退出日志；
2. 抽取最终 exception type/message；
3. 定位最后一个用户代码 frame；
4. 保存用户行源代码和前后上下文；
5. 保留内部 raise site，用于关联源码 guard；
6. 将动态值、绝对路径、数字等规范化为稳定 error signature。

### 8.4 AST API Resolver

解析策略按优先级：

1. 用户 frame 对应 AST `Call/Attribute`；
2. import alias：`gs`、`genesis` 和直接 import；
3. 简单赋值流：`sensor = scene.add_sensor(...)` 后的 `sensor.xxx()`；
4. traceback 内部 API frame；
5. 错误文本中的类、函数和参数；
6. `key_apis/retrieval_trace` 只作为弱先验，不作为确定证据。

Resolver 输出 `primary_api_id/related_api_ids/confidence/resolution_method`。低置信映射不得自动生成 C。

## 9. Loop B 完善方案

### 9.1 先聚类，再生成候选

聚类键建议：

```text
category
+ normalized_error_signature
+ primary_api_id / bad_symbol
+ normalized_ast_pattern
```

同一 cluster 中：

- 保留代表性最强的 1–3 个 evidence；
- 统计任务数、代码变体数和 Genesis 版本；
- 单次重复运行不重复增加独立支持数；
- runner/环境失败在聚类前排除。

### 9.2 B 候选生成

生成顺序：

1. 确定性模式库生成已知修正；
2. API catalog/source 查找候选替代 API；
3. LLM 根据精简 evidence 生成 `bad/correction/why`；
4. 结构化校验与 compactness lint；
5. 静态或 replay verification；
6. 人工审核。

LLM 输入不应包含整批长 traceback，而应包含：

- 用户失败行及局部代码；
- 标准化错误；
- primary/related APIs；
- 对应 API 摘要、签名和源码事实；
- 同 cluster 的少量变体。

### 9.3 B 质量 Gate

硬门槛：

- 非环境/runner/资源问题；
- 有稳定 trigger；
- 有具体 bad pattern；
- correction 不为空且不是泛化建议；
- 与源码/API catalog 不冲突；
- 可以说明适用版本；
- 没有泄漏 benchmark 标准答案或任务专属常量；
- rendered text 通过长度和格式检查；
- 与已有 B/C 不重复或冲突。

单条 evidence 可以产生候选，但只有满足以下任一条件才可批准：

- 源码或签名可直接证明；
- corrected replay 通过；
- 多个独立任务重复出现并经人工确认。

### 9.4 B 的触发方式

按阶段采用不同触发键：

#### 首次生成前

```text
retrieved/predicted API IDs
  -> 反查与这些 API 相关的高优先级 error memories
```

只选择与当前 API 集和 domain tag 同时匹配的少量 B。

#### Draft 生成后

```text
AST symbols + keyword + call order
  -> 精确匹配 bad_symbols / ast_patterns
```

此阶段比用户 query 向量检索更可靠，适合触发不存在的属性、错误参数和生命周期模式。

#### 执行失败后

```text
error_signature + API ID
  -> 精确查找修复记忆
```

用于任务内定向修复，不应重新注入无关 error memories。

#### 语义 fallback

只有结构化键无命中时，才使用 query/code/error 文本的混合向量检索。

## 10. Loop C 完善方案

### 10.1 一候选一约束

当前“一个 API 候选包含 constraints 数组”的形式改为：

```text
一个 candidate_id
  -> 一个 api_id
  -> 一个 rule
```

优点：

- 单条批准或拒绝；
- 单条冲突、废弃和版本更新；
- 单条 exposure/utility 归因；
- 同一 API 的约束不再捆绑发布。

兼容导出时仍可按 API 聚合为 `constraints: []`。

### 10.2 C 规则类型

首版覆盖：

```text
unsupported_keyword
required_argument
argument_relation
numeric_range
numeric_divisibility
call_order
lifecycle
object_type
return_type
solver_compatibility
asset_contract
deprecation_replacement
```

### 10.3 Pattern Registry

建立可测试的规则注册表，而不是把所有逻辑堆在 `_heuristic_constraints()`：

```python
ConstraintPattern(
    name="scene_unbuilt_guard",
    error_signature="GenesisException:scene_already_built",
    rule_type="lifecycle",
    build=...,
    verify=...,
)
```

首批必须覆盖当前数据中的：

- unrecognized/unsupported keyword；
- missing/duplicate/extra arguments；
- module/object missing attribute；
- `Scene is already built`；
- Terrain divisibility；
- solver precision；
- solver boundary；
- morph/material/coupler compatibility；
- Options/Pydantic 字段别名和废弃字段。

### 10.4 源码事实校验

对 C 候选增加 source corroboration：

- 构造器字段来自 Options/Pydantic model fields；
- 参数关系来自源码显式 `if ... raise_exception(...)`；
- lifecycle 来自 `assert_built/assert_unbuilt` 等 decorator；
- deprecation 来自源码 warning/deprecated metadata；
- 版本 scope 来自当前 Genesis version/commit。

源码 guard 能证明事实时，候选可标记 `source_verified`；仍需人工批准后才能 active。

### 10.5 C 的冲突与优先级

- 同一 `api_id + fact_key + scope` 只能有一个 active 事实版本；
- 新候选与现有约束方向相反时进入 conflict review；
- deprecated 或版本不适用的约束不展示；
- 每 API 可存储多条约束，但 serving 时按任务相关性、严重度、验证等级和历史 utility 选 top 3；
- 不在样本不足阶段引入复杂加权模型，首版使用可解释的分层排序。

排序优先级：

```text
版本适用
> 与当前代码/API 条件匹配
> replay_verified
> source_verified
> 高严重度/高复发
> 历史 utility
```

## 11. LLM 的职责边界

LLM 可以：

- 从结构化 diagnosis 生成 root-cause 建议；
- 将复杂证据压缩为简洁 B/C 文本；
- 建议 correction 或替代 API；
- 评估候选是否原子、可操作、冗余；
- 为人工审核提供理由。

LLM 不可以：

- 单独把候选变成 approved/active；
- 覆盖确定性签名、源码或 replay 事实；
- 在没有 API/source 证据时编造替代方案；
- 把环境失败包装成 API 知识；
- 修改生产 snapshot。

模型输出使用严格 JSON schema，并记录：

- provider/model/version；
- prompt template version；
- input diagnosis IDs；
- 原始 response；
- 解析/校验结果。

## 12. Verification 设计

### 12.1 验证等级

```text
unverified
static_verified
source_verified
replay_verified
cross_task_verified
```

- `static_verified`：AST、symbol、signature 或字段检查能证明。
- `source_verified`：Genesis 源码 guard 能直接证明规则。
- `replay_verified`：原代码稳定失败，修正版在同环境通过目标检查。
- `cross_task_verified`：在多个独立任务/代码变体中成立。

### 12.2 Replay 的因果要求

最小 replay pair：

```text
同一环境 + 同一任务 + 尽量小的代码改动
failing version  -> 目标错误稳定出现
corrected version -> 目标错误消失，且没有被更早的新错误遮蔽
```

不能仅以 return code 0 作为所有约束的验证；至少要确认：

- 原 error signature 消失；
- 程序执行越过原失败点；
- 没有立即出现等价错误；
- 对需要物理语义的规则，等待后续 validator，不伪称 verified physics。

### 12.3 无法自动 patch 的候选

如果修正需要较大代码重构：

- 允许 `source_verified + human approved` 进入 shadow；
- 暂不自动 active；
- 收集未来自然使用和人工修正证据后再晋级。

## 13. 审核与状态机

统一状态：

```text
proposed
  -> verifying
  -> verified
  -> approved
  -> shadow
  -> active
  -> deprecated

任意阶段可进入 rejected / quarantined / conflicted
```

审核界面/Markdown 应直接展示：

- rendered B/C；
- primary/related APIs；
- user code line；
- 标准化错误；
- source/signature 证据；
- support count 与任务数；
- verification 结果；
- 与现有知识的重复/冲突提示；
- token 长度和 compactness lint；
- approve/reject/edit/split/merge 决策。

审核决策必须追加记录，不覆盖候选历史。

## 14. Serving 与 Agent 集成

### 14.1 C 使用 runtime overlay

API 文档分为：

```text
Static API Catalog
+ Active Constraint Overlay(api_id, snapshot_id, task context)
= Serving API Document
```

约束不写回静态 API index，不参与 API embedding 文本。API 被检索后再按 ID 附加约束，避免每次约束更新都重建 API 向量库。

### 14.2 B 使用结构化 Trigger Index

建议维护：

- `api_id -> memory_ids`；
- `bad_symbol -> memory_ids`；
- `error_signature -> memory_ids`；
- `ast_pattern -> memory_ids`；
- 语义向量索引作为 fallback。

### 14.3 Prompt 分区

不要再把 error memory 混在普通 `api_docs` 中。建议 prompt 使用独立区块：

```text
--- API Documentation ---
...

--- API Guards ---
[con_xxx] Call Scene.add_force_field(...) before scene.build().

--- Common Failure Patterns ---
[err_xxx]
Avoid: ...
Use: ...
Why: ...
```

系统 prompt 明确优先级：

```text
源码验证的 API Guards
> Reference Code
> API Docs
> Error Memory suggestions
> 模型猜测（禁止）
```

如果 Error Memory 与 API Guard 冲突，使用经过版本匹配的 API Guard，并记录 conflict。

### 14.4 Draft 静态检查

首次生成后、执行前：

1. `ast.parse`；
2. 提取 API、keyword、对象方法和调用顺序；
3. exact match B triggers；
4. 检查 C constraints；
5. 若命中高置信错误，进行一次定向修正；
6. 保存修正前后 code hash 和触发的 knowledge IDs。

这一步能减少无意义执行，也比首次 prompt 注入大量错误记忆更精准。

### 14.5 知识归因字段

每个 attempt 至少记录：

```json
{
  "retrieved_knowledge_ids": ["api:...", "err_...", "con_..."],
  "prompted_knowledge_ids": ["err_...", "con_..."],
  "draft_matched_knowledge_ids": ["err_..."],
  "repair_applied_knowledge_ids": ["err_..."],
  "violated_constraint_ids": [],
  "outcome": "process_passed"
}
```

当前 error query 结果必须携带稳定 memory ID；C overlay 也必须逐条携带 constraint ID，而不是只记录 API ID。

## 15. 存储、发布与回滚

### 15.1 Canonical 与 Derived 分离

```text
Canonical
  feedback.db
  workspace/runs/... immutable artifacts
  knowledge_snapshots/<snapshot_id>/

Derived / Compatibility
  genesis_error_memory.json
  api_constraint.json
  trigger indexes
  Chroma collections
```

推荐使用 SQLite 保存 diagnosis、cluster、candidate、verification、decision 和 snapshot metadata；JSON/JSONL 继续作为导入、导出和审计格式。

### 15.2 发布流程

1. 从 approved + version-compatible 知识生成临时 snapshot；
2. schema、引用、重复、冲突和 compactness 检查；
3. 构建 B trigger index 与 C overlay；
4. 跑 golden suite 和 canary benchmark；
5. 原子更新 `current_snapshot`；
6. 保留上一版本；
7. 发布失败时不影响当前 serving；
8. 支持一条命令回滚。

### 15.3 Shadow 模式

新知识先进入 shadow：

- 正常执行检索和匹配；
- 记录“如果 active 会不会被展示/触发”；
- 不进入 Agent prompt；
- 用于估计覆盖、误触发和 token 成本；
- 达到门槛后再 active。

## 16. 质量与效果指标

### 16.1 数据可信度

| 指标 | 初始门槛 |
|---|---:|
| Prompt 终态记录完整率 | 100% |
| Artifact 可读取率 | 100% |
| runner/环境失败进入 B/C | 0 |
| 重复处理新增候选 | 0 |

### 16.2 Diagnosis 与候选质量

| 指标 | 初始门槛 |
|---|---:|
| Golden API 错误 diagnosis recall | >= 90% |
| API mapping precision | >= 95% |
| 错误 API 映射率 | <= 2% |
| C 原子化率 | 100% |
| B 有明确 correction | 100% |
| active 知识具备验证或源码证明 | 100% |
| 环境知识污染率 | 0 |

### 16.3 简洁性

| 指标 | 初始门槛 |
|---|---:|
| B serving text | <= 120 tokens/条 |
| C serving text | <= 60 tokens/条 |
| 单 API 默认展示 C | <= 3 条 |
| 首次生成展示 B | <= 2 条 |
| compactness lint 通过率 | 100% |

### 16.4 在线触发与效用

| 指标 | 含义 |
|---|---|
| exposure count | 知识被展示次数 |
| structural match rate | 展示知识与 draft API/AST 真正匹配的比例 |
| adoption rate | draft/repair 是否遵循 correction/constraint |
| same-signature recurrence | 展示知识后仍出现同类错误的比例 |
| targeted repair success | 定向修复后原错误消失比例 |
| pass@1 / pass@k lift | 相对 baseline 的执行提升 |
| context token delta | B/C 增加的上下文成本 |
| irrelevant warning rate | 展示但与代码不相关的知识比例 |

首版上线建议门槛：

- trigger precision >= 80%；
- targeted 同类错误相对下降 >= 25%；
- canary Pass@1 回归不超过 2 个百分点；
- 平均上下文 token 增量在预设预算内；
- 不出现经确认的错误事实 active。

门槛应在得到真实 baseline 后调整，不在数据不足时构建复杂的综合评分模型。

### 16.5 A/B 评估矩阵

固定模型、temperature、基础 RAG 和任务集合，至少比较：

| 组别 | B | C |
|---|---:|---:|
| Baseline | 关闭 | 关闭 |
| C-only | 关闭 | 开启 |
| B-only | 开启 | 关闭 |
| B+C | 开启 | 开启 |

评估集分为：

1. **Targeted holdout**：针对已知错误簇设计但不复用原始失败代码；
2. **General canary**：覆盖原 benchmark，监控无关任务回归；
3. **Replay suite**：验证具体 failing/corrected pair；
4. **Shadow traffic**：估计真实触发率和 token 成本。

避免用产生知识的同一条代码同时充当最终效果测试，防止记忆式过拟合。

## 17. 分阶段实施路线

### Phase 0R：重新止血与可信基线（1–2 天）

目标：修复新发现的 runner 污染，重新建立可信执行事实。

任务：

1. 修改 `feedback_loop/run_and_collect.py` 的生成脚本文件名和 import 隔离。
2. 将 runner 抽为共享实现，逐步替换 `benchmark/pipeline.py` 和 `workspace/run_existing_query_code.py`。
3. 新增 `runner_infrastructure` 分类和 circular-import shadowing 规则。
4. 增加 runner self-check 和回归测试。
5. 将 `online-full` 中 29 条污染事件 quarantine。
6. 使用修复后的 runner 重放现有 100 份代码。
7. 输出新的执行漏斗报告。

验收：

- `code.py` shadowing fixture 稳定通过；
- runner 污染进入 B/C 为 0；
- 相同代码重复运行的分类结果稳定；
- 可信重放日志可被现有 processor 读取。

### Phase 1：统一 Diagnosis 与聚类（3–5 天）

目标：B/C 共用唯一诊断核心。

建议新增：

```text
feedback_loop/diagnosis/
  models.py
  traceback_parser.py
  normalizer.py
  api_resolver.py
  classifier.py
  clusterer.py
```

任务：

1. 定义 FailureDiagnosis schema 和稳定 ID。
2. 实现 final exception、user frame、source guard 解析。
3. AST API resolver 覆盖直接调用、alias 和简单变量流。
4. 建立错误签名规范化。
5. 按 diagnosis 聚类并生成 funnel/rejection reason。
6. 用当前 29 个错误签名建立 golden fixtures。
7. processor 改为先生成 diagnosis，再路由 B/C。

验收：

- 当前 70 个错误事件都有明确处理状态；
- 29 个 runner 事件全部排除；
- seeded API 错误映射 precision >= 95%；
- 重复 event 不重复生成 cluster。

### Phase 2：B/C Candidate Builder 与简洁性 Gate（3–5 天）

目标：提高产出质量并控制审核成本。

建议新增：

```text
feedback_loop/candidates/
  error_memory_builder.py
  api_constraint_builder.py
  constraint_patterns.py
  compactness.py
  dedup.py
```

任务：

1. B 改为一 cluster 一候选。
2. C 改为一候选一原子约束。
3. 建立首批 deterministic pattern registry。
4. 增加 source/signature corroboration。
5. 引入可选 LLM synthesis，严格 JSON 输出。
6. 增加 compactness/actionability/redundancy lint。
7. review.md 展示 cluster、源码证据、验证等级和 token 长度。

验收：

- `online-full` 重放中高价值 lifecycle/numeric/compatibility 错误不再被静默丢弃；
- B 审核数量从 event 数量收敛到错误簇数量；
- 所有候选能给出明确生成或拒绝原因；
- serving projection 100% 满足长度规范。

### Phase 3：Serving Overlay、精准触发与归因（3–5 天）

目标：让高质量知识真正以低噪声方式到达 Agent。

任务：

1. `rag_engine.py` 增加 C overlay 查询，不再把新约束写回 API embedding 文本。
2. 建立 B 的 API/symbol/error/AST trigger index。
3. error 检索结果携带稳定 memory ID。
4. `agent.py` 将 API Guards 和 Error Memories 分区展示。
5. 增加全局 token budget 和 top-k 选择。
6. 增加 draft AST audit 与一次定向修正接口。
7. attempt 记录 retrieved/prompted/matched/applied/violated IDs。

验收：

- 能回答某条 B/C 是否被展示和命中；
- API 被选中后可即时看到 active C，无需重建 API embedding；
- B exact trigger 在目标 fixture 中召回，非目标 fixture 不误触发；
- Agent 上下文增量受预算控制。

### Phase 4：Verification、审核状态与版本化发布（4–7 天）

目标：建立可证明、可回滚的正式知识发布链路。

任务：

1. 引入 SQLite workflow store。
2. 实现 failing/corrected replay pair。
3. 记录 review decision、reviewer、notes 和 candidate version。
4. 建立 snapshot publisher 和 current pointer。
5. 发布前运行 schema/conflict/golden/canary。
6. 增加 shadow、active、deprecated 和 rollback。
7. 继续导出旧 JSON，保持兼容。

验收：

- 未 verified/approved 的知识无法 active；
- 发布中途失败不影响当前 snapshot；
- 可以回滚到上一 snapshot；
- candidate -> evidence -> verification -> decision -> snapshot 全链路可追溯。

### Phase 5：效用评估与持续治理（持续）

任务：

1. 运行 Baseline/C-only/B-only/B+C 对照实验。
2. 统计 exposure、match、adoption、recurrence 和 pass lift。
3. 对低效、误触发或导致回归的知识降级/废弃。
4. 根据真实数据调整 top-k、token budget 和批准门槛。
5. 扩充 deterministic patterns 和 targeted holdout。
6. 在数据充足后再考虑 utility 排序模型。

## 18. 文件级改造清单

| 文件/模块 | 主要改造 |
|---|---|
| `feedback_loop/run_and_collect.py` | 安全脚本名、共享 runner、完整环境与 runner version |
| `feedback_loop/failure_classifier.py` | 新 taxonomy、runner/asset/engine 边界 |
| `feedback_loop/processor.py` | diagnosis 驱动、cluster 候选、原子 C、拒绝原因 |
| `feedback_loop/loop_b/judge.py` | 由原始证据收集迁移为结构化 B builder/兼容层 |
| `feedback_loop/loop_c/constraint_builder.py` | 拆分 parser、resolver、pattern registry；旧入口 deprecated |
| `feedback_loop/gates.py` | 展示 verification、cluster、冲突和 compactness；决策写入 store |
| `feedback_loop/utils.py` | 规范化 ID、事实去重、兼容导出 |
| `rag_engine.py` | B trigger index、C overlay、稳定知识 ID、upsert/snapshot |
| `agent.py` | 独立 Guard/Memory prompt、token budget、draft audit、归因 |
| `benchmark/pipeline.py` | 共用 runner，记录知识 exposure/adoption |
| `benchmark/metrics.py` | B/C trigger、recurrence、repair、token 和 lift 指标 |
| `feedback_loop/tests/` | runner、diagnosis、routing、compactness、replay、snapshot 测试 |

## 19. 当前数据迁移方案

### 19.1 `online-full`

1. 原始日志和 artifacts 永久保留；
2. 标记 29 个 runner-shadowing event 为 quarantined；
3. 不批准当前 68 个 B 候选；
4. 当前 4 个 C 候选重新进入新 diagnosis/builder，不直接批量批准；
5. 修复 runner 后重放全部现有代码；
6. 使用新结果重新生成 B/C；
7. 新旧候选做 diff，形成迁移报告。

### 19.2 现有 9 条 Error Memory

- 导入为 `legacy_reviewed`；
- 人工补充 `api_ids/bad_symbols/ast_pattern/scope`；
- 与源码和当前版本复核；
- 先 shadow 观测 trigger；
- 通过 targeted suite 后 active。

### 19.3 现有 approved constraints

- 为每条约束拆分独立 constraint ID；
- 补充 api_id、rule_type、scope 和 evidence；
- 无法证明来源的条目标记 `legacy_unverified`；
- 不删除历史内容，但未验证条目不自动进入新 snapshot。

### 19.4 旧 JSON 与 Chroma

- 迁移期继续导出 `genesis_error_memory.json` 和 `api_constraint.json`；
- 新 canonical store 是事实来源；
- Chroma 是可重建派生索引；
- 新发布流程稳定前不直接清空旧库。

## 20. 测试矩阵

### 20.1 Runner

- 生成文件名与 `code/json/random/typing/torch` 等模块冲突；
- stdout/stderr partial output；
- Timeout；
- 进程崩溃；
- 相同代码重放；
- 不同 cwd 和资产目录；
- 环境 fingerprint 与 runner version。

### 20.2 Diagnosis

- direct `gs.*` call；
- `scene.*` method；
- import alias；
- assignment 后的对象方法；
- module/object missing attribute；
- duplicated Genesis error line；
- 多 exception event；
- API lifecycle decorator；
- engine internal 与 API usage 区分。

### 20.3 B/C Builder

- 多 event 聚成一个 B；
- 同事实不同文本去重；
- 一个 diagnosis 正确路由 B/C/Discard；
- C 一候选一规则；
- correction 为空时拒绝 B；
- C 无 api_id 或低置信映射时拒绝；
- source conflict；
- version scope conflict；
- compactness 超限；
- LLM 非法 JSON fallback。

### 20.4 Verification/Publishing

- failing replay 稳定复现；
- corrected replay 消除目标 signature；
- 未审核候选禁止发布；
- snapshot 中途失败回滚；
- overlay 与 trigger index 引用完整；
- 旧 snapshot 可恢复；
- 相同发布输入生成稳定 snapshot 内容。

### 20.5 Serving/Agent

- API 命中后附加正确 C；
- 不相关 API 不附加 C；
- AST pattern 精确触发 B；
- B/C ID 写入 attempt trace；
- prompt token budget；
- 冲突知识不同时展示；
- inactive/shadow/deprecated 知识不进入正式 prompt。

## 21. 风险与控制

| 风险 | 控制措施 |
|---|---|
| LLM 生成错误修正 | 源码/签名/replay 校验 + 人工批准 |
| 知识过多使 prompt 变长 | 原子规则、top-k、全局 token budget、draft 后精准注入 |
| B/C 重复表达同一事实 | 统一 diagnosis、明确路由、事实键去重 |
| 单次偶发错误被泛化 | source/replay/multi-task 三种验证路径 |
| API 版本变化导致旧知识错误 | version scope、snapshot、deprecated、回滚 |
| 向量检索误触发错误记忆 | 结构化 exact trigger 优先，向量只 fallback |
| replay 修正引入新错误 | 检查是否越过原失败点并记录新 signature |
| 发布导致线上回归 | shadow + canary + 原子 snapshot 切换 |
| 工作流过度复杂 | 分阶段落地；首版不引入知识图谱、自动发布或复杂评分模型 |

## 22. 明确暂不做

- 不追求自动从所有失败生成知识；
- 不允许 LLM 自动批准或直接写生产库；
- 不做 GraphRAG、知识图谱或多 Agent 审核编排；
- 不做 embedding 微调；
- 不在 Phase 1 设计复杂 utility 加权模型；
- 不在缺少 Physics Validator 时重新开启 Loop A；
- 不把所有 B/C 在首次生成时全量塞入 prompt；
- 不以候选数量作为闭环主要 KPI。

## 23. Definition of Done

Feedback Loop B/C 第一阶段生产化完成，需要同时满足：

1. runner/环境污染不会进入 B/C；
2. 每个 eligible failure 有唯一 diagnosis 和明确处理结果；
3. B 按错误簇生成，C 一候选一原子规则；
4. active B 有稳定 trigger、bad/correction/why 和版本范围；
5. active C 有已知 api_id、原子 rule、适用条件和证据；
6. 所有 active 知识经过 source/static/replay 中至少一种验证及人工批准；
7. B 使用结构化触发，C 使用 API overlay；
8. Agent prompt 满足 B/C token budget；
9. 每条知识可追踪 retrieved -> prompted -> matched/applied -> outcome；
10. 发布支持 shadow、canary、snapshot 和回滚；
11. targeted suite 的同类错误率显著下降，general canary 无不可接受回归；
12. 旧 JSON 数据可兼容导出，迁移过程不丢失历史证据。

## 24. 推荐的下一执行切片

为了最快获得可靠收益，下一轮不要同时实现 SQLite、LLM Judge 和完整发布系统。建议先完成一个可独立验收的切片：

```text
安全 runner
+ runner failure quarantine
+ FailureDiagnosis v1
+ error signature 聚类
+ 6 类高价值 C pattern
+ B cluster review 输出
+ 每阶段 funnel/rejection reason
```

具体顺序：

1. 修复 `code.py` shadowing；
2. 无模型重放现有 100 份代码；
3. 建立新的可信漏斗；
4. 实现 user frame + API mapping；
5. 为 `Scene is already built`、Terrain divisibility、SAP precision、primitive plane compatibility、solver boundary、unrecognized attribute 建立 deterministic patterns；
6. B 从 68 个 event 候选改为 cluster 候选；
7. 生成新 review 文档，让人工先评估质量和简洁性；
8. 质量达到预期后，再进入 overlay、精准触发和 replay verification。

这个切片能够直接回答三个关键问题：

- 清理执行器污染后，真实可学习失败有多少？
- B/C 能否稳定生成简洁、准确、可操作的知识？
- 在不改生产检索链路前，候选质量是否已经值得继续投入？

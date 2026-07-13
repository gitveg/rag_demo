# Feedback Loop v2 设计方案

> 日期：2026-07-10  
> 范围：`rag_demo/feedback_loop`、执行采集、RAG 知识消费、benchmark 联动  
> 状态：Phase 0 已于 2026-07-11 实施；Phase 1 及以后尚未实施

## 1. 结论

当前模块已经证明“执行结果可以离线回流”，但还没有形成可信的学习闭环。核心缺口不是再增加几条正则或调低候选门槛，而是四项基础能力尚未成立：

1. 执行事实不完整、不可稳定重放。
2. 代码/API 失败与依赖、资源、超时等环境失败没有可靠分层。
3. 候选知识只有解释，没有通过修正代码重放得到因果验证。
4. 正式知识、审核状态和 Chroma 派生索引之间没有版本化发布与回滚边界。

v2 应将系统的基本单元从“A/B/C 三条脚本产物”改成：

```text
Immutable Attempt
    -> Failure Diagnosis
    -> Typed Candidate
    -> Replay Verification
    -> Human Decision
    -> Versioned Knowledge Snapshot
    -> Retrieval Attribution
    -> Utility Update / Rollback
```

Loop A/B/C 可以保留为用户可理解的知识类型，但不再各自重复解析一次执行日志。一次失败应先产生唯一诊断，再由诊断派生零个或多个候选。

## 2. 现状证据

### 2.1 本轮 100 条执行数据

| 分片 | 记录 | 成功 | 失败 | B 候选 | C 候选 |
|---|---:|---:|---:|---:|---:|
| part1 | 30 | 18 | 12 | 11 | 0 |
| part2 | 30 | 15 | 15 | 13 | 0 |
| part3 | 30 | 4 | 26 | 26 | 0 |
| part4 | 10 | 2 | 8 | 6 | 0 |
| 合计 | 100 | 39 | 61 | 56 | 0 |

失败粗分类：

| 类别 | 数量 | 当前处理结果 |
|---|---:|---|
| 普通 traceback | 47 | 进入 B，C 未识别 |
| 虚拟内存分配失败 | 9 | 错误进入 B 候选 |
| Timeout | 4 | 被 B 过滤 |
| 缺少 LuisaRenderPy | 1 | 被 B 过滤 |

C 回路为 0 的直接原因已定位：`run_and_collect.py` 保存了最多 8000 字符的 `concise_error`，但 `collect_loop_c()` 只读取最多 500/2000 字符的 `stdout/stderr`。用同一批日志的 `concise_error` 重新做只读解析，可得到：

- 56 个 error event；
- 34 个可映射 event；
- 6 条启发式约束，覆盖 Box、Terrain、IMU、Lidar 四个 API。

这说明 C 回路并非“数据中没有约束”，而是采集契约和消费契约不一致。

### 2.2 已确认的高风险实现

1. `run_and_collect.py:226-229`：生成失败直接 `continue`，没有执行记录。系统无法区分未运行与成功，也无法统计生成基础设施失败。
2. `run_and_collect.py:76-89`：只要进程返回 0 且无 traceback，就通过 `best_effort_success` 判成功，场景是否构建不再是必要条件。
3. `run_and_collect.py:134-142`：Timeout 丢失子进程已经产生的 stdout/stderr，无法判断是编译慢、仿真慢、死循环还是渲染阻塞。
4. `processor.py:225-233`：C 回路不使用 `concise_error`，实际 61 个失败全部解析为 0 event。
5. `processor.py:354-363`：A 候选写入待审 JSON 时把完整 `unit` 裁成 `unit_id/title/all_apis` 三个字段；之后批准会把这个残缺对象写入正式知识库。
6. `processor.py:529-552`：进度只由“日志 basename + 行偏移”决定。日志重命名、覆盖、截断或同名路径会造成重复处理或永久漏处理。
7. `processor.py:430-460`：批准写库没有 schema 校验、原子提交、锁、发布版本或回滚；默认 `--ids all` 也不符合 fail-closed。
8. `gates.py`：Gate 只负责生成 Markdown，`review()` 永远 pending；文档仍称其为 LLM 双层门控，设计和实现已经漂移。
9. `rag_engine.py:319-393`：JSON 到 Chroma 使用 `add`，依赖全量删库重建；发布失败会留下不可用或半完成状态。
10. `rag_engine.py:739-749`：错误记忆按用户/HyDE query 做向量召回。用户任务描述与“错误模式”天然不相似，触发键设计不合理。
11. `rag_engine.py:227-228`：约束只有合并进 API index 并重建 Chroma 后才生效，审核库和在线消费之间存在双写与版本漂移。
12. `benchmark/pipeline.py` 与 `feedback_loop/run_and_collect.py` 各自实现执行器，`constraint_builder.py` 还有第三份旧实现，成功标准、超时和日志字段不一致。
13. 项目没有针对 feedback loop 的自动化测试；当前 `tests/test.py` 是一次性索引脚本，不是测试套件。

## 3. 第一性原则

### 3.1 闭环的目的

闭环不是“把失败写进库”，而是让未来任务以可测量、可归因、可回滚的方式减少同类失败。

一条知识要进入生产消费面，至少必须满足：

1. **真实**：来自完整、不可变的执行证据。
2. **因果**：应用修正后，在同等环境中能让目标失败消失。
3. **可泛化**：描述的是 API/生命周期/物理规则，而不是单次机器状态。
4. **可寻址**：未来生成过程能通过 API、错误签名或代码模式精确触发。
5. **可撤销**：每条知识有来源、版本、状态和回滚路径。
6. **有效**：上线后能观测被检索、被采用以及对执行结果的影响。

### 3.2 两个闭环必须分开

```text
任务内修复闭环（秒/分钟）
draft -> static check -> execute -> diagnose -> targeted retrieval -> repair

跨任务学习闭环（小时/天）
attempts -> aggregate evidence -> verify -> review -> publish -> evaluate
```

任务内修复可以使用低置信诊断帮助本次重试，但不得直接写正式知识。跨任务学习只接收经过验证的候选。

### 3.3 “成功”不是单一布尔值

建议结果状态至少拆成：

```text
generation_failed
static_invalid
infra_failed
dependency_failed
resource_failed
timed_out
runtime_failed
process_passed
physics_failed
verified_passed
```

`process_passed` 只说明退出码和异常正常；只有满足任务断言或物理验证后才能称为 `verified_passed`。Loop A 在物理验证器可用前继续默认关闭。

### 3.4 保留并复用现有资产

v2 不是推倒重写。以下能力方向正确，应收敛到新数据契约中：

- `api_id_normalize.py` 的公开 API alias 归一化；
- `indexers/indexer_code.py` 的 AST API 提取；
- `benchmark/query.json` 的任务、复杂度和 expected APIs；
- `benchmark/metrics.py` 的 RAG 命中、Pass@k 和 incremental 指标；
- 待审候选与人工批准的 fail-closed 思路；
- RAG 返回 `type/content/meta` 的统一条目格式；
- Agent 已开始记录的 `knowledge_ids` 检索归因信息；
- 当前 100 条执行日志，作为迁移和回归 fixture 的真实样本。

需要替换的是这些能力之间脆弱的文件/脚本耦合，而不是它们各自已经验证过的核心逻辑。

### 3.5 历史决策边界

现有两份问题回应文档确认了三项产品决策，v2 继续保留：

1. constraint 必须先进入 staging，审核通过后才能发布；
2. Gate 必须 fail-closed；
3. 可以使用更强模型辅助分析高风险候选。

强模型 Judge 的权限边界是“生成诊断、修正或审核建议”，不能单独把候选变为 active。模型、prompt、输出和版本应作为 review evidence 留存；正式发布仍要求确定性校验、重放验证和显式决策。

## 4. 目标架构

```text
Prompt / Benchmark Task
        |
        v
Generation Service ---- retrieval trace ----> RAG Service
        |
        v
Static Inspector
  - AST syntax
  - API symbol resolution
  - signature/argument check
  - constraint reverse lookup
        |
        v
Isolated Runner ------ immutable artifacts ------> Attempt Store
        |                                         |
        v                                         v
Outcome Classifier ------------------------> Failure Diagnosis
                                                  |
                         +------------------------+---------------------+
                         |                        |                     |
                         v                        v                     v
                  Error Memory             API Constraint        Recipe/Skill
                   Candidate                 Candidate             Candidate
                         |                        |                     |
                         +------------------------+---------------------+
                                                  |
                                                  v
                                         Replay Verification
                                                  |
                                                  v
                                           Human Review
                                                  |
                                                  v
                                      Knowledge Snapshot Publisher
                                                  |
                         +------------------------+---------------------+
                         |                        |                     |
                         v                        v                     v
                  API overlay            Pattern lookup        Vector recipe index
```

## 5. 核心数据契约

v2 首先建立数据契约，再写处理算法。建议使用标准库 `dataclasses` + 显式校验，工作流状态存 SQLite；继续导出 JSON/JSONL 兼容现有工具。暂不引入新的服务或重型数据库。

### 5.1 ExecutionAttempt

```json
{
  "schema_version": 2,
  "event_id": "evt_<sha256>",
  "run_id": "run_<uuid>",
  "task_id": "s1_camera_medium_002",
  "prompt_index": 54,
  "prompt_hash": "sha256:...",
  "attempt": 1,
  "stage": "execution",
  "code_artifact": {
    "path": "workspace/runs/<run_id>/<task_id>/attempt_1/code.py",
    "sha256": "..."
  },
  "retrieval_trace": [
    {"knowledge_id": "api:...", "rank": 1, "score": 0.82, "snapshot_id": "kb_..."}
  ],
  "environment": {
    "python": "3.10.x",
    "genesis_version": "...",
    "genesis_commit": "...",
    "backend": "cpu",
    "os": "windows",
    "gpu": "...",
    "asset_root": "..."
  },
  "outcome": "runtime_failed",
  "returncode": 1,
  "exception": {
    "type": "GenesisException",
    "message": "Unrecognized attribute: vel",
    "user_frame": {"file": "code.py", "line": 10, "source": "gs.morphs.Box(..., vel=...)"}
  },
  "signals": {},
  "artifacts": {
    "stdout": "stdout.txt",
    "stderr": "stderr.txt",
    "traceback": "traceback.txt"
  },
  "timing": {"generation_s": 12.3, "execution_s": 9.7}
}
```

要求：

- 每个 prompt 无论在哪个阶段失败，都必须有终态 event。
- event ID 由 run/task/attempt/stage/code hash 生成，不依赖时间戳或日志行号。
- stdout/stderr 原文保存为 artifact；结构化记录只保存摘要和引用。
- 代码按 attempt 不可变保存，不能再让同一个 `task_id.py` 被后续运行覆盖。
- task ID 必须经过白名单化，禁止路径穿越。

### 5.2 FailureDiagnosis

```json
{
  "diagnosis_id": "diag_<sha256>",
  "event_id": "evt_...",
  "category": "api_signature",
  "root_cause": "Box does not accept vel",
  "api_ids": ["genesis.options.morphs.Box"],
  "error_signature": "GenesisException:Unrecognized attribute:vel",
  "evidence": [
    {"artifact": "traceback.txt", "start": 120, "end": 380},
    {"artifact": "code.py", "line": 10}
  ],
  "confidence": 0.98,
  "generalizable": true,
  "retryable": true,
  "classifier_version": "failure_classifier_v1"
}
```

推荐分类：

- `generation_infra`
- `syntax`
- `python_logic`
- `dependency`
- `asset_path`
- `resource`
- `timeout`
- `api_symbol`
- `api_signature`
- `api_lifecycle`
- `engine_internal`
- `physics_semantic`
- `unknown`

只有 `api_symbol/api_signature/api_lifecycle` 默认允许派生 B/C；其他类别必须有额外证据。资源、依赖和基础设施失败只进入运行健康度，不进入生成知识。

### 5.3 KnowledgeCandidate

```json
{
  "candidate_id": "cand_<normalized_payload_hash>",
  "kind": "api_constraint",
  "status": "verified",
  "payload": {},
  "evidence_ids": ["diag_..."],
  "verification": {
    "status": "passed",
    "failing_replay_event": "evt_...",
    "corrected_replay_event": "evt_..."
  },
  "created_at": "...",
  "review": null,
  "supersedes": null
}
```

状态机：

```text
proposed -> verifying -> verified -> approved -> shadow -> active
                  |           |          |          |
                  v           v          v          v
               rejected    rejected   rejected   deprecated
```

状态变更必须追加 decision 记录，不覆盖历史。

## 6. 诊断与候选生成

### 6.1 先分类，再派生

现有 B/C 会各自读取原始日志，容易对同一失败给出不一致判断。v2 的流程是：

1. Outcome Classifier 先排除生成、依赖、资源、Timeout 和引擎基础设施问题。
2. Traceback Parser 找到最后一个用户代码 frame，而不是只匹配最终错误行。
3. AST Inspector 根据 frame 行号定位具体 Call/Attribute 节点。
4. API Resolver 将公开 alias 解析为规范 API ID。
5. Diagnosis Builder 生成一次结构化根因。
6. B/C Candidate Builders 只消费 diagnosis，不再解析原始日志。

### 6.2 Loop B：错误记忆

B 不应只是 `bad_pattern/correction/explanation` 文本，还应包含未来触发所需的结构化键：

```json
{
  "bad_pattern": "gs.morphs.Box(..., vel=...)",
  "correction": "set velocity on the built entity through a supported state/control API",
  "explanation": "vel is not a Box morph constructor attribute",
  "api_ids": ["genesis.options.morphs.Box"],
  "error_signature": "Unrecognized attribute:vel",
  "ast_pattern": "Call(api=Box, keyword=vel)",
  "scope": {"genesis_version": "..."}
}
```

入库 Gate：

- 必须是可泛化的代码/API 失败；
- 必须有精确代码证据；
- 必须有可执行修正，而不只是“查看文档”；
- 原失败可在干净 worker 中复现；
- 修正版本在同一环境中通过目标检查；
- 与已有 pattern 做规范化 AST 去重，而非纯字符串去重。

### 6.3 Loop C：API 约束

C 是 API 的事实层，标准要高于 B：

- `api_id` 必须存在于当前静态 API 索引；
- 规则必须明确到参数、调用顺序、对象类型或生命周期；
- 优先用签名/源代码/最小复现验证；
- 约束带版本范围和证据；
- 同一 API 的冲突约束不能自动合并，必须进入冲突审核。

首版启发式覆盖：

- unexpected/unrecognized keyword；
- missing/duplicate/extra positional argument；
- object has no attribute；
- call before/after `scene.build()`；
- morph/material 类型兼容性；
- asset 参数名与路径规则。

当前日志中的六条 `Unrecognized attribute` 应成为 v2 的固定回归样例。

### 6.4 Loop A：Recipe/Skill

“退出码为 0”不能证明代码值得沉淀。Loop A 改为 Recipe Candidate，并继续默认关闭，直到具备：

- process pass；
- 任务断言或 Physics Validator pass；
- 干净环境至少两次重放一致；
- 资产可访问、路径可移植；
- 无 benchmark answer leakage；
- 与已有 recipe 在代码、API 集、任务意图三个维度均有新信息。

长期可以从 verified recipe 抽取参数化 skill，但不应在 v2 第一阶段实施。

## 7. 在线消费方式

### 7.1 错误记忆改为 API/代码模式反查

错误记忆不再主要依赖用户 query 的向量相似度。推荐顺序：

1. 初次检索得到的 API 集合反查相关约束和错误模式。
2. 生成 draft 后 AST 提取实际 API/keyword，再精确反查。
3. 执行失败后按 error signature + API ID 精确反查。
4. 只有缺少结构化键时才使用语义检索 fallback。

### 7.2 约束作为 overlay，不写回静态 API 源文件

把 API 文档拆成：

```text
Static API Catalog      由 indexer 生成，版本化、只读
Reviewed Constraint DB 人工/验证闭环产生，按 api_id 查询
Serving API Document   请求时组合前两者
```

这样新约束批准后无需修改 `genesis_api_index.json`，也无需为了文本约束重建 API embedding。API 被选中后再附加约束，语义召回与事实发布解耦。

### 7.3 Draft 静态检查

执行前新增廉价的 compiler-like pass：

1. `ast.parse`；
2. 提取 `gs.*`、`scene.*` 调用；
3. 对照 API 索引解析 symbol；
4. 使用 signature 检查显式 keyword；
5. 注入命中 API 的约束和高价值 error memory；
6. 若发现未知 symbol/keyword，定向修复一次再执行。

这会比把所有约束塞进首次 prompt 更省 token，也更容易归因。

## 8. 存储与发布

### 8.1 Canonical 与 Derived 分离

```text
Canonical
  feedback.db                 event/diagnosis/candidate/decision
  workspace/runs/...          code/stdout/stderr/video 等不可变 artifacts
  knowledge_snapshots/...     已发布知识快照

Derived
  api_constraint.json         兼容导出
  genesis_error_memory.json   兼容导出
  genesis_chroma_db           可重建检索索引
```

SQLite 使用 WAL、事务和唯一键解决并发及幂等；JSON 只作为导出物，不再承担工作流数据库职责。

迁移时不得直接清空现有 `api_constraint.json` 或错误记忆。先生成只读历史 snapshot，再逐条标记为 `retained/quarantined/deprecated`。无法证明来源或包含环境噪音的条目进入 quarantine，不参与 serving，但保留审计证据。

### 8.2 发布事务

1. 从 approved candidates 生成新 snapshot 到临时目录。
2. 运行 schema、引用完整性、重复、冲突检查。
3. 构建/更新派生索引。
4. 在 canary benchmark 上验证。
5. 原子切换 `current_snapshot` 指针。
6. 保留上一版本，可一条命令回滚。

Chroma collection 名建议包含 snapshot ID，避免先删生产 collection 再重建。

## 9. 建议模块结构

```text
feedback_loop/
  cli.py
  config.py
  domain/
    models.py
    enums.py
    validation.py
  runtime/
    collector.py
    runner.py
    artifacts.py
    environment.py
  diagnosis/
    classifier.py
    traceback_parser.py
    api_mapper.py
  candidates/
    error_memory.py
    api_constraint.py
    recipe.py
  verification/
    replay.py
    static_checks.py
  review/
    service.py
    renderer.py
  storage/
    event_store.py
    candidate_store.py
    snapshot_store.py
    json_exports.py
  serving/
    overlays.py
    triggers.py
  tests/
    fixtures/
    test_collector.py
    test_classifier.py
    test_api_mapper.py
    test_candidates.py
    test_promotion.py
```

`benchmark` 和 `feedback_loop` 必须共用 `runtime/runner.py`，不再维护多份执行语义。

## 10. 分阶段迁移

### Phase 0：止血与建立回归基线（2-3 天）

实施状态：**已完成代码改造与离线回放验证**。当前 16 个自动化测试通过；旧 100 条日志回放得到 46 条 B 候选、4 个 C API 候选和 6 条 C 约束，明确的资源/依赖/超时失败已隔离。由于当前 DashScope 凭据不可用，全新在线生成运行仍待有效凭据后验证。

目标：不改知识策略，先保证当前数据可信。

1. 所有生成/执行终态都写日志，新增 `schema_version/run_id/event_id/prompt_index/code_hash`。
2. C 改用完整 traceback/`concise_error`，补当前六条约束的回归 fixture。
3. 新增失败分类，隔离 OOM、dependency、timeout；现有 9 条内存失败不得进入 B。
4. 修复 A 候选序列化丢字段，但保持 A 默认关闭。
5. `--ids` 默认改为空；批准前做 schema/API ID/必填字段校验。
6. JSON 写入改为临时文件 + `os.replace`，写前备份。
7. 进度由 event ID 去重替代 basename offset。
8. 更新 README，使其与“人工审核、无 LLM gate”一致。

停止条件：当前 100 条日志可重复处理，候选数量稳定；C 不再为 0；基础设施失败泄漏为 0；重复运行不产生重复候选。

### Phase 1：统一事件与诊断核心（约 1 周）

1. 引入 domain models 和 SQLite event store。
2. 合并三个执行器，保存不可变 artifacts 和环境指纹。
3. 建立 failure taxonomy、traceback user frame 和 AST API 定位。
4. processor 改为 diagnosis 驱动，B/C 不再各自解析日志。
5. 稳定 candidate ID 和显式状态机。
6. 把现有 JSONL/候选迁移器作为一次性兼容入口。

停止条件：采集、诊断和候选生成均有单元/集成测试；任意 event 可追溯到代码、环境和原始输出。

### Phase 2：验证与版本化发布（约 1 周）

1. 增加 failing/corrected replay verification。
2. 审核决策入库，记录 reviewer、notes、时间和候选版本。
3. 生成 knowledge snapshot，支持 canary 和回滚。
4. API 约束改为 serving overlay；错误记忆改为结构化反查。
5. Chroma 使用 snapshot collection 或 upsert，不再直接删除当前库。

停止条件：未经 verified + approved 的候选无法进入 serving；发布失败不影响当前 snapshot；可回滚到上一版本。

### Phase 3：任务内修复与效用归因（1-2 周）

1. Draft AST/API/signature 检查。
2. 执行失败后的 targeted retrieval + 一次定向 repair。
3. 记录知识条目的 retrieved/adopted/outcome attribution。
4. benchmark 激活 incremental RAG、修复收益和成本指标。
5. 根据 Wilson lower bound 或保守先验维护 utility，不直接用小样本成功率排序。

停止条件：能回答“哪条知识在哪个 attempt 被采用，并使什么错误消失”；targeted suite 的 Pass@1/修复率有稳定提升，canary 无明显回归。

### Phase 4：Physics Validator 与 Recipe（后续）

1. NaN/Inf、穿透、运动方向、状态变化等确定性检查。
2. 引入 `physics_failed/verified_passed`。
3. 在验证信号成熟后重新开启 Loop A。
4. 从 verified recipes 提取参数化 skills。

## 11. 测试矩阵

### 11.1 单元测试

- JSONL 尾行损坏、日志截断、重复 event、同名日志。
- 生成失败、空代码、syntax error、returncode 0 但未构建场景。
- Timeout 保留 partial output。
- OOM、缺依赖、CUDA/Taichi 内部错误不产生 B/C。
- unexpected keyword、unrecognized attribute、missing argument、lifecycle error 能定位正确 API。
- API alias 规范化和 user-frame AST 映射。
- A/B/C candidate schema round-trip 不丢字段。
- 审批未知/重复/空 ID fail closed。
- snapshot 发布中途失败可回滚。

### 11.2 集成测试

构造最小脚本组：

1. 一个正确的刚体场景。
2. `Box(vel=...)` API 参数失败及其修正版。
3. `Terrain(terrain_config=...)` 失败及其修正版。
4. `add_camera` 生命周期失败及其修正版。
5. 缺依赖、Timeout、模拟资源失败。
6. process pass 但任务断言失败。

每组验证 event -> diagnosis -> candidate -> replay -> review -> serving 的完整链路。

### 11.3 发布验收指标

| 指标 | v2 初始门槛 |
|---|---:|
| Prompt 终态记录完整率 | 100% |
| 环境/资源失败进入知识候选 | 0 |
| Seeded API 失败诊断召回 | >= 90% |
| 错误 API 映射率 | <= 2% |
| 重复处理新增候选数 | 0 |
| 未审核候选进入 serving | 0 |
| Snapshot 发布可回滚 | 100% |
| Targeted repair suite 改善 | 必须为正 |
| Canary Pass@1 回归 | 不超过预设容忍阈值 |

不要把总体 RAG hit rate 当作反馈闭环的唯一指标。更重要的是 diagnosis precision、repair success、candidate utility、知识污染率和发布回归。

## 12. 明确暂不做的事

- 不在 Phase 0/1 自动开启 Loop A。
- 不让 LLM 单独决定根因或正式入库。
- 不自动把 constraint 写回静态 API index。
- 不以全文向量搜索作为错误记忆的主要触发方式。
- 不先做 embedding 微调、GraphRAG 或复杂多代理编排。
- 不在没有 Physics Validator 时把 exit code 0 称为物理正确。

## 13. 推荐的首个实现切片

第一个 PR 只做“可信采集 + 正确 C 回路 + 基础分类”，避免同时改存储和在线检索：

1. 新建 v2 event schema 和兼容 writer。
2. 修改 `run_and_collect.py`，记录全部终态并保留完整 artifacts。
3. 新建 failure classifier，先覆盖 timeout/dependency/resource/runtime。
4. 修改 C 输入为结构化 exception + code snapshot。
5. 为当前六条约束、九条内存错误和四条 timeout 建 golden tests。
6. 修复审批 fail-closed 和 A 序列化数据丢失。

这个切片完成后，再引入 SQLite 和 snapshot 发布。这样每一步都有独立收益，也能用当前 100 条日志做确定性回归。

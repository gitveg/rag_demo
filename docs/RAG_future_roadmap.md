# 物理仿真 Agent 时代，RAG 的出路：趋势分析与研究规划

> 日期：2026-06-11
> 性质：战略分析 + 研究规划（面向工程可用性 + 论文创新性）
> 前置文档：`RAG_imorovement_Claude.md`（战术级改进清单）、`benchmark_improvement_plan.md`

---

## 〇、核心问题

> 在 Agent 时代，RAG 已经成熟甚至"不够用"。前沿 Agent 产品（Claude Code 等）不再把 RAG 放在重点，转而关注 Harness、记忆等。针对我们的物理仿真 Agent，RAG 的出路在哪？

**一句话结论先行**：RAG 作为"一次性检索 pipeline"确实在贬值，但作为**检索与经验基座**反而在升值。我们的出路不是继续打磨检索精度，而是把 `rag_demo` 升级为物理仿真 Agent 的**领域经验层（Domain Experience Layer）**——以执行反馈为 ground truth，统一管理知识、记忆、技能三类资产，并以工具形态供 Agent 主动调用。我们已经无意中走在这条路上（feedback_loop 三回路就是雏形），需要的是把它**正名、补全、并提炼出可发表的创新点**。

---

## 一、前沿趋势调研

### 趋势 1：Coding Agent 放弃向量 RAG，转向 Agentic Search——但要看清适用边界

Claude Code 的事实（来自其作者 Boris Cherny 在 HN 的公开说明）：早期版本确实用了 RAG + 本地向量库，后来发现 **agentic search（grep/glob/read 工具循环）大幅胜出**，原因是：精确性（代码需要精确符号匹配，embedding 引入模糊误报）、新鲜度（索引随编辑漂移）、简单性（无需 embedding pipeline / 向量库 / 同步设施）、隐私安全。2026 年的实证研究显示 agentic 关键词搜索能达到 RAG 90% 以上的效果且零运维。

但**这个结论有明确的适用前提**，业界共识（SmartScope 等分析）是：

- agentic search 赢在 **code exploration** 场景：代码已存在于磁盘上，任务是"找到它"
- 语义检索仍然赢在：**概念性查询、超大规模库、非代码知识、自然语言到代码的语义鸿沟**
- 2026 年的实践答案不是二选一，而是 **agentic 为骨架、语义索引为补充、context engineering 为粘合**

参考：[Claude Code Doesn't Index Your Codebase](https://vadim.blog/claude-code-no-indexing)、[Settling the RAG Debate](https://smartscope.blog/en/ai-development/practices/rag-debate-agentic-search-code-exploration/)

### 趋势 2：Agentic RAG——检索从 pipeline 变成决策循环

2026 年的 SoK 论文（[arXiv:2603.07379](https://arxiv.org/abs/2603.07379)）把 agentic RAG 形式化为**有限时域 POMDP**：检索不再是"query 进、context 出"的一次性函数，而是 Agent 在多步决策中**自主决定何时检索、检索什么、检索几次、何时停止**。配套变化：

- **检索即工具（Retrieval as Tool）**：检索器以 tool 形态暴露给 LLM，由模型决定调用策略；MCP 成为事实标准的检索工具接口
- **评估范式转移**：从 output-only 指标（hit rate）转向 **trajectory 级评估**（整条决策链的可靠性）
- 已识别的系统性风险：复合幻觉传播、**记忆投毒（memory poisoning）**、检索失配、成本失控（agentic RAG 运行时 token 成本是静态 RAG 的 3–10 倍）

### 趋势 3：记忆系统成为新主战场——演化路径"存储 → 反思 → 经验"

2026 年初的记忆机制综述（[From Storage to Experience](https://www.preprints.org/manuscript/202601.0618)）提出了清晰的三阶段演化框架：

1. **Storage（存储）**：保存原始轨迹（对话历史、执行日志）
2. **Reflection（反思）**：对轨迹做精炼（总结、错误分析、打分入库）
3. **Experience（经验）**：跨轨迹抽象，产出可复用的**启发式准则（Heuristic Guidelines）**和**程序性原语（Procedural Primitives）**

前沿系统的落点都在第三阶段：

- **技能库（Skill Library）**：Voyager 的经典范式——Agent 把成功经验编译成可执行函数（`mineIron()`），下次直接调用而非重新推导。SkillX（2026）自动从成功轨迹提炼三级技能层次，使弱模型 Agent 在 AppWorld/τ²-Bench 上绝对提升约 10%，且技能库可跨 Agent 迁移
- **结构化记忆**：A-Mem 的 Zettelkasten 式链接笔记（token 减少 85–93%）、Mem0 的多信号融合检索（语义 + BM25 + 实体匹配单一融合分数）
- **关键洞察**：记忆系统的核心技术栈（embedding、向量库、混合检索、rerank）**与 RAG 完全同源**——区别只在于：存什么（轨迹/经验 vs 文档）、谁写入（Agent 自己 vs 人工灌库）、怎么演化（持续生长 vs 静态）

### 趋势 4：私有/低资源库的代码生成——"检索到了也不会用"

这条线对我们最直接相关：

- **To See is Not to Master**（[arXiv:2603.15159](https://arxiv.org/abs/2603.15159)，PriCoder）：实证发现**即使把准确的私有库 API 文档喂进 context，LLM 仍然无法有效调用**——检索增强存在天花板。其方案是基于 API 使用图的数据合成 + 微调，pass@1 提升 20%+
- **Amazon CloudAPIBench**：发现文档增强（DAG）对**低频 API 有效、对高频 API 反而有害**（干扰模型已掌握的参数化知识）→ **选择性检索（selective retrieval）**：先验证生成结果中的 API 是否存在于索引，未命中再触发检索
- 共同结论：对于 Genesis 这类训练语料中几乎不存在的领域库，**"检索注入"和"参数内化（微调）"是互补的两条腿**，且检索的最佳触发时机是"生成后验证失败时"而非"生成前一股脑注入"

---

## 二、关键判断：Claude Code 的结论为什么不能照搬到我们场景

把我们的场景和 Claude Code 的场景逐项对比，会发现**我们恰好落在向量检索仍然不可替代的那一侧**：

| 维度 | Claude Code（code exploration） | 我们（物理仿真代码生成） |
|---|---|---|
| 目标代码 | 已存在于磁盘，找到即可 | **不存在，需要无中生有** |
| 查询形态 | 符号/字符串精确匹配为主 | **自然语言物理场景描述**（"让水流冲击沙堆"），语义鸿沟真实存在 |
| LLM 参数知识 | 主流语言/框架，模型烂熟 | **Genesis 是低资源库**，模型参数里没有或全是幻觉 |
| 知识新鲜度 | 代码随编辑秒变，索引必然过期 | API 文档/范例库**低频变化**，索引过期问题轻微 |
| ground truth | 编译/测试 | **物理仿真执行**——比单元测试更丰富的反馈信号 |

所以正确的解读是：**Claude Code 不是证明了"检索没用"，而是证明了"当模型参数知识足够强、目标信息可精确寻址时，不需要语义索引"**。我们两个前提都不满足——这恰恰是 RAG 技术栈在 Agent 时代仍然成立的少数高价值场景（低资源领域库 + 自然语言到代码的跨模态检索）。

但同时，趋势 2/3/4 给我们的警示也是真实的：

1. **一次性 pipeline 形态过时了**——应该变成 Agent 可自主调用的工具集与决策循环
2. **静态知识库形态过时了**——应该变成随执行持续生长的经验库（我们的 feedback_loop 已经在做，方向完全正确）
3. **"检索注入"有天花板**——对照 PriCoder 的发现，我们 benchmark 中"检索命中但生成仍失败"的 case 就是这个天花板的体现，需要技能化/微调来突破

---

## 三、定位升级：从"RAG 模块"到"领域经验层（Domain Experience Layer）"

### 3.1 重新命名我们已有的资产

用趋势 3 的"记忆分型"视角盘点 `rag_demo`，会发现我们已经持有一个准记忆系统的全部要素，只是没用这套语言来组织：

| 已有资产 | 记忆学对应 | 当前阶段 |
|---|---|---|
| `genesis_api_index.json` + Core API 注入 | **语义记忆**（事实性知识） | 成熟 |
| `genesis_knowledge_units.json`（代码范例+文档聚合） | **情景记忆**（具体成功案例） | 成熟 |
| `genesis_error_memory.json` + 回路 B | **教训记忆**（负面经验） | 管道通，利用率低（n_error=0） |
| `api_constraint.json` + 回路 C | **程序性规则**（使用约束） | 管道通 |
| feedback_loop 三回路 + 双层门控 | **Reflection 阶段**（轨迹精炼） | 雏形完整 |
| —（缺失） | **程序性技能**（参数化可复用原语） | **未开始 ← 最大空白** |
| —（缺失) | **效用元数据**（每条记忆的实战战绩） | **未开始** |

对照"Storage → Reflection → Experience"框架：我们已稳定在 Reflection 阶段，**下一步的主线就是向 Experience 阶段演进**——这同时是工程提升点和论文创新点。

### 3.2 目标架构

```
                    物理仿真 Agent（Planner / Coder / Debugger）
                                      │
                       检索工具集（Retrieval as Tools）
          ┌──────────┬──────────┬─────┴────┬───────────┬──────────┐
     search_units  lookup_api  check_     search_     grep_
     (语义检索)    (精确寻址)  constraints  skills     examples
          │           │        (规则反查)  (技能检索)  (字面搜索)
          └───────────┴──────────┴──────────┴───────────┴──────────┘
                                      │
                          领域经验层（统一存储 + 生命周期管理）
        ┌────────────┬────────────┬────────────┬────────────┐
        │ 语义记忆    │ 情景记忆    │ 教训/规则   │ 程序性技能  │ ← 新增
        │ API 文档    │ 知识单元    │ 错误+约束   │ 参数化原语  │
        └────────────┴────────────┴────────────┴────────────┘
                  每条记忆携带：utility_score / 来源 / 版本 / 战绩
                                      ▲
                            执行反馈闭环（已有三回路）
                       + 物理合理性验证（新增，见创新点 B）
                       + 回归门禁（新知识入库前跑 benchmark 子集）
```

与现状的三个本质区别：

1. **接口形态**：`search()` 单入口 → 多个细粒度工具，Agent 在生成循环中按需调用（含"生成后符号验证失败 → 定向检索"的 selective retrieval，呼应趋势 4）
2. **资产形态**：新增第四类资产——**参数化技能**，从知识单元（整段代码示例）进化为可组合的函数级原语
3. **生命周期**：每条记忆带效用元数据，检索排序融合实战战绩，配合淘汰/合并机制对抗记忆膨胀与投毒

---

## 四、论文创新点分析

结合调研，我们相对学界的**独特资产**是：① 真实物理引擎执行环境（ground truth 不是 LLM 自评）；② 已运转的执行反馈闭环；③ 77 任务 × 14 域 × 3 复杂度的 benchmark 与全套消融基建。基于此，三个候选创新点按推荐度排序：

### 创新点 A（最推荐）：物理感知的执行反馈——超越 Pass@k 的经验信号

**Gap**：现有 coding agent 的反馈信号止步于"跑通/报错"（exit code 级）。但物理仿真的特殊性在于：**代码跑通 ≠ 物理正确**——物体穿透、能量爆炸、NaN 速度场、该动的不动，这些都是 exit code 0 下的静默失败。学界目前没有把"物理状态合理性"作为代码生成反馈信号的工作。

**做法**：
- 构建**物理合理性验证器（Physics Validator）**：执行后自动检查仿真状态——穿透深度、能量/动量守恒残差、NaN/Inf 检测、运动学合理性（用户要"下落"的物体位移是否为负）等，产出结构化的 `physics_report`
- 可叠加 VLM 对渲染帧的语义级判断（"水是否真的流出来了"）作为高层信号
- 该信号回流三处：① 反馈闭环的入库门控（只有物理正确的代码才能成为知识单元/技能）；② Agent 的修复循环（物理报告作为 debug 上下文）；③ benchmark 新指标 **PhysPass@k**（执行通过且物理合理）

**为什么强**：领域特性化最彻底、别人最难复制（需要物理引擎 + 闭环基建）、且把我们 benchmark 的故事一并升级。

### 创新点 B：执行验证的技能库——面向低资源物理库的经验抽象

**Gap**：技能库工作（Voyager / SkillX / AWM）集中在游戏、Web、工具调用环境，技能的"正确性"靠任务奖励或 LLM 评判；没有工作在**低资源科学计算库**上做"执行+物理双重验证"的技能合成。

**做法**：
- 从 feedback_loop 回路 A 的成功代码中，自动提炼**参数化技能**：如 `setup_mpm_fluid(viscosity, resolution) -> Scene`、`attach_camera_tracking(entity)`，附带适用条件与组合约束
- 技能三级结构（呼应 SkillX）：领域技能（流体场景搭建）→ 复合技能（流固耦合模板）→ 原子技能（单 API 正确调用模式）
- 跨域复杂任务（benchmark 中 `cross_domain_complex`，正是当前失败重灾区）改为**技能组合**而非从零生成
- 检索排序融合 `utility_score`（被采用次数 × 下游 PhysPass 率）——"经验加权检索"本身可作为独立消融点

**为什么强**：直接对标 2026 最热的 Experience 阶段叙事，且我们的验证信号（真实执行+物理校验)比所有现有技能库工作的信号都硬。

### 创新点 C：Benchmark 贡献——GenesisAgentBench

把现有 77 任务 benchmark 升级为可发表的评测集：自然语言物理场景 → 可执行仿真代码，指标含 RAG Hit Rate / Pass@k / PhysPass@k / token 效率，覆盖 14 个物理域 × 3 复杂度。作为论文的评测章节或独立的 resource track 投稿。低资源库评测正是社区痛点（PriCoder 为此专门新建了两个 benchmark）。

### 推荐的论文叙事

> **"Execution-Grounded Experience Learning for Physics Simulation Agents"**
> ——一个以真实物理执行为 ground truth 的自进化经验层：执行反馈闭环（已有）+ 物理感知验证（A）+ 技能抽象与经验加权检索（B），在 GenesisAgentBench（C）上验证。
> 核心 claim：在低资源领域库上，**经验层（自进化技能+教训）显著优于静态 RAG**，且**物理感知信号显著优于 exit-code 信号**。

这个叙事的好处：A、B、C 三点可以独立成章也可以合并成一篇系统论文；每一点都有现成基建托底，不是从零开始。

---

## 五、路线图

### 阶段 0：补完基本盘（≈2 周，与论文无直接关系但是地基）

1. 激活执行评测（Pass@k 目前永远是 null）——`benchmark_improvement_plan.md` P0.2
2. 生成后符号验证 + selective retrieval（`RAG_imorovement_Claude.md` 创新 1；趋势 4 证实这是正确路线）
3. 检索归因日志（记录"检索条目 → 是否被代码采用 → 是否跑通"），为 utility_score 积累数据

### 阶段 1：物理验证器 + PhysPass@k（≈3-4 周，创新点 A）

1. 实现 Physics Validator v1：NaN/Inf、穿透、位移方向、能量残差四类检查（Genesis 的 scene/entity state API 都能拿到）
2. 接入 benchmark → 产出 PhysPass@k；接入 feedback_loop 门控 → 提升入库质量
3. 用 77 任务跑出 "Pass@k vs PhysPass@k" 的 gap 数据——这个 gap 本身就是论文 motivation 图

### 阶段 2：技能库 + 经验加权检索（≈4-6 周，创新点 B）

1. 技能提炼器：从回路 A 产出的成功代码中切分参数化函数（LLM 抽象 + AST 校验 + 执行回归验证）
2. 新 collection `genesis_skills`，技能检索工具 `search_skills`
3. utility_score 融入排序：`score = α·semantic + β·utility`，消融对比
4. 跨域任务走"技能组合"生成路径，对比从零生成

### 阶段 3：检索工具化 + Agent 循环改造（≈3 周，可与阶段 2 并行）

1. 把 `search()` 拆成细粒度工具集（search_units / lookup_api / check_constraints / search_skills），由 Agent 在循环中自主调用
2. 教训/约束改为 **API 反查注入**（检索结果含 `add_camera` → 自动附带其约束），替代 n_error 语义检索
3. trajectory 级日志，支撑论文的行为分析章节

### 阶段 4：实验与写作（≈4 周）

消融矩阵：静态 RAG baseline / +物理验证 / +技能库 / +经验加权 / 完整系统 × 14 域 × 3 复杂度。主指标 PhysPass@k，辅以 token 成本（回应 agentic RAG 成本 3-10 倍的质疑）。

### 明确不做的事

- **不做通用记忆框架**（Mem0/A-Mem 已饱和，没有物理引擎我们无优势）
- **暂不做 embedding 微调**（PriCoder 路线的数据合成+微调工程量大，作为论文的 future work 或第二篇）
- **不追求检索指标本身的 SOTA**（Hit Rate 70%→75% 没有故事，PhysPass@k 才有）

---

## 六、风险与对策

| 风险 | 对策 |
|---|---|
| 物理验证器误判（把正确代码判为物理错误） | 验证规则保守化：只报确定性失败（NaN、深穿透）；模糊项只警告不拦截 |
| 技能库引入记忆投毒/膨胀（趋势 2 已警示） | 入库门禁（回归 benchmark）+ utility 衰减淘汰 + 技能数量上限 |
| agentic 循环 token 成本失控 | 保留单次检索快速路径；只对 complex 任务启用多步循环；报告成本指标 |
| 创新点 A/B 被并行工作抢发 | A 的物理验证器领域壁垒高、被抢发概率低；尽早把 PhysPass@k 的 gap 数据跑出来确立优先权 |

---

## 附：本文档引用的关键资料

- Claude Code 放弃 RAG 的一手说明：[vadim.blog/claude-code-no-indexing](https://vadim.blog/claude-code-no-indexing)
- Agentic vs 语义检索的边界分析：[SmartScope: Settling the RAG Debate](https://smartscope.blog/en/ai-development/practices/rag-debate-agentic-search-code-exploration/)
- Agentic RAG 形式化（POMDP）与风险：[SoK: Agentic RAG, arXiv:2603.07379](https://arxiv.org/abs/2603.07379)
- 记忆机制三阶段演化综述：[From Storage to Experience (2026)](https://www.preprints.org/manuscript/202601.0618)
- 技能库前沿：[SkillX (zjunlp)](https://github.com/zjunlp/SkillX)；记忆论文清单：[Awesome-Memory-for-Agents](https://github.com/TsinghuaC3I/Awesome-Memory-for-Agents)
- 低资源库代码生成的检索天花板：[To See is Not to Master, arXiv:2603.15159](https://arxiv.org/abs/2603.15159)
- 选择性检索（高频 API 检索有害）：[Amazon: On Mitigating Code LLM Hallucinations with API Documentation](https://assets.amazon.science/8f/83/7407a5634a80a39e82b52ae935fe/on-mitigating-code-llm-hallucinations-with-api-documentation.pdf)

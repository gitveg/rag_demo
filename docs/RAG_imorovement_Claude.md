我已经通读了 `rag_demo` 的核心代码和文档。先说结论：你做的确实很全面了——五路 collection、HyDE + 知识单元、Symbol Boost 混排、Core API 注入、距离阈值、benchmark 体系（Hit Rate / Pass@k）、三回路执行反馈闭环，这套架构已经超过大多数生产级 RAG。但站在「代码生成 Agent 的 RAG」这个视角，还有不少真正有价值的空间。

---

## 一、工程上的改进（按 ROI 排序）

**1. Reranker 已写好但没接进主链路**

`reranker.py`（gte-rerank-v2）已经实现，但 `rag_search_params.md` 里明确写着「当前 rag_demo 未实现，保留参数」。这是现成的低垂果实：把 `rerank=True` 路径接通，配合 `rerank_oversample` 超采样（先召回 2 倍再裁剪），直接跑一轮 benchmark 对比。交叉编码器对 unit 路径的精度提升通常很明显。

**2. 增量灌库，替代全量重建**

反馈闭环的 Step 3 是 `python rag_engine.py` 全量重灌。知识库自增长后这会越来越慢，而且有"重灌期间检索不可用"的窗口。改成基于内容 hash 的 upsert（Chroma 原生支持），只更新变化的条目。

**3. KB 变更的回归门禁（CI for Knowledge）**

反馈闭环会自动入库新知识，但**新知识可能让检索变差**（稀释、语义碰撞）。建议：每次入库后自动跑一遍 benchmark 子集，Hit Rate 下降超过阈值就回滚本批次。你已经有 `run_benchmark_batch.py`，只差把它变成入库流程的 gate——这和你 feedback_loop 的双层审核门控思路一脉相承，相当于第三层门控。

**4. 固定检索预算 → token 预算感知的自适应打包**

现在 `n_units=5, n_api=6, n_code=1...` 是固定的。更好的方式是给一个总 token 预算，按 rerank 分数贪心装箱：简单 query 少占上下文，复杂 query 多给配额。`metrics.py` 里已经有 tiktoken 计数逻辑，可以直接复用。

**5. 检索归因（Attribution）日志**

记录「检索回来的每个 unit/API，最终有没有出现在生成代码里、代码有没有跑通」。这是免费的相关性标注数据，能回答两个关键问题：哪些知识单元是"占位不干活"的（可以降权或淘汰），哪些 query 类型的检索在拖后腿。你有执行闭环，做这个的成本极低，但大多数 RAG 系统做不了。

**6. HyDE 的延迟与稳定性**

HyDE 每次 query 多一次 LLM 调用。可以加：① query 归一化后的重写缓存；② HyDE 生成失败时自动降级到 translate 路径；③ 多路检索（unit + core API + error）并行化。

---

## 二、创新设计上的方向

**1. 生成后符号验证 + 按需二次检索（最推荐）**

你的 `agent.py` prompt 里写了 "DO NOT invent APIs"，但这是靠 LLM 自律。可以改成机制保证：

- 生成代码后，AST 解析提取所有 `gs.xxx.yyy` 符号
- 与 `genesis_api_index.json` 比对（你已有 `api_id_normalize.py` 做归一化）
- 未命中的符号 → 定向二次检索其文档 → 带着补充上下文重新生成或修正

这本质是把 RAG 从"一次性检索"变成"生成驱动的按需检索"，直接打击幻觉 API 这个代码生成 Agent 的头号死因，而且是纯静态检查，比执行反馈快得多、便宜得多——相当于在执行闭环前面加了一道"编译期"闭环。

**2. 效用加权排序（Utility-based Ranking）**

现在排序只看语义相似度。但你有别人没有的数据：**每个知识单元被引用后的下游执行成功率**。给每个 unit 维护一个 `utility_score`（被检索次数、被采用次数、关联代码的 Pass 率），融合进最终排序：`score = α·semantic + β·utility`。这是把执行闭环从"知识生产"延伸到"检索排序"，可以写成一个很漂亮的创新点。

**3. API 共现图谱 / 约束链检索（轻量 GraphRAG)**

从 `genesis_code_index.json` 的 key_apis 统计 API 共现矩阵，构建依赖关系（比如 `add_camera` 总是先于 `build()`、`MPMOptions` 总是伴随特定 material）。检索命中某个 API 后，做一跳图扩展，把"必须配套的 API + 回路 C 产出的约束"一起注入。解决的痛点：cross-domain 复杂任务里 LLM 漏掉配套调用——你 `stage1_manual/domain_failure_analysis.md` 里应该已经观察到这类失败。

**4. 复杂任务的查询分解（Multi-hop Retrieval）**

benchmark 里 `cross_domain_complex` 这类任务，单次 HyDE 生成的伪代码很难覆盖全部子系统。可以让 LLM 先把任务拆成子任务（如"FEM 布料 + 机械臂抓取 + 相机录制"），每个子任务独立走 unit 检索，再去重合并。对 simple 任务跳过分解，只对分类为 complex 的启用，控制成本。

**5. 错误记忆的"约束感知注入"**

默认 `n_error=0`，说明按 query 语义检索错误记忆效果不好——这符合直觉：用户的 query 和"坑"的描述天然不相似。更好的触发方式：**按已检索到的 API 集合反查**错误记忆和回路 C 约束（"你要用 add_camera？那注意这条约束"）。匹配键从语义换成 API ID，精准且零误伤。

**6. 领域自适应 Embedding 微调**

你已经积累了大量 (query, expected_apis, 命中/未命中) 的 benchmark 数据和失败分析。这些就是现成的训练对：用对比学习（正例 = 命中的 unit，难负例 = 高分但未命中的 unit）LoRA 微调一个开源 embedding 模型（bge/gte），替代通用的 text-embedding-v4。这是论文/报告里最有"创新"色彩的一项，但工程量最大，建议放最后。

---

## 三、如果只做三件事

1. **生成后符号验证 + 按需二次检索**（创新 1）——对 Pass@k 提升最直接
2. **接通 Reranker + 跑 A/B**（工程 1）——半天工作量，现成模块
3. **效用加权排序**（创新 2）——把你最独特的执行闭环优势变成检索能力

整体看，你的检索侧（召回）已经做得很厚了，边际收益在递减；下一阶段的增量主要在**检索与生成/执行的耦合处**——验证、归因、效用回流。这也正好是你这套系统相对通用 RAG 最有差异化的地方。
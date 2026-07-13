# 混合检索实验报告：从 BM25 到 Symbol Boost

> **模块**：`rag_demo/hybrid_search.py` + `rag_engine.py`
> **日期**：2026-06-07

---

## 一、背景

### 1.1 问题

当前 RAG 系统的检索完全依赖稠密向量检索（DashScope text-embedding-v4 + ChromaDB 余弦相似度）。RAG 优化路线图和 Opus 专家咨询均指出，纯语义检索在**专有名词和 API 名称**上的召回能力偏弱——如 `MJCF`、`Rasterizer`、`Terrain`、`SPH.Liquid` 等 token，其语义向量与用户查询的相似度可能不够高，导致检索遗漏。

弱域（drone 0.75、terrain 0.76、sensor 0.76）的核心瓶颈正是此类**词汇级精确匹配**失败，而非语义理解不足。

### 1.2 优化目标

在 Dense 检索之上引入精确匹配通道，提升 API 名称等专有 token 的召回，同时不损害已有 Dense 检索的正确率。

### 1.3 探索路径

我们依次尝试了两种方案：

| 方案 | 方法 | 结果 |
|---|---|---|
| 方案 A：BM25 + Dense + RRF | 通用稀疏检索融合 | ❌ Hit Rate 下降 0.0113 |
| **方案 B：API Symbol Boost** | **结构化元数据精确匹配** | **✅ Hit Rate 提升 0.0066，零回归** |

以下按背景→方案 A→方案 B→最终结论的结构展开。

---

## 二、方案 A：BM25 稀疏检索 + Dense + RRF 融合

### 2.1 设计

业界标准的混合检索方案：

```
Query ──┬── [Dense: ChromaDB 余弦] ──┐
        │                             ├── [加权 RRF 融合] ──> Final Results
        └── [Sparse: BM25Okapi] ─────┘
```

**Dense 路径**：现有 ChromaDB 余弦相似度检索（语义匹配）。

**Sparse 路径**：BM25 关键词检索。为适配中英文混合 + Python 代码的文档特点，设计了专门的分词器（HybridTokenizer）：

| 分词策略 | 示例 |
|---|---|
| 点分标识符拆分 | `genesis.morphs.Sphere` → `genesis`, `morphs`, `sphere` |
| CamelCase 拆分 | `ViewerOptions` → `viewer`, `options` |
| jieba 中文分词 | `刚体球体下落` → `刚体`, `球体`, `下落` |
| Genesis 领域词典 | `MJCF`, `Rasterizer`, `URDF` 等作为完整词保留 |

**融合**：加权 RRF（`score = w_d × 1/(k+rank_d) + w_s × 1/(k+rank_s)`），默认 `w_d=0.7, w_s=0.3`，使 Dense 路径拥有更高话语权。

BM25 索引在 `GenesisRAG` 初始化时从 ChromaDB 已有数据构建，知识单元 101 条 + API 654 条，纯内存无需持久化，构建耗时 < 1 秒。

### 2.2 测试结果

100 条 benchmark 查询（覆盖 rigid_body、soft_body、fluid、robot、drone、terrain、sensor 等域），每条含 `expected_apis`（平均 10.6 个 API）。

| 配置 | 命中 APIs | Hit Rate | 差异 |
|---|---|---|---|
| 纯 Dense | 569/1057 | 0.5383 | baseline |
| BM25 (0.5/0.5) | 563/1057 | 0.5326 | -6 |
| BM25 (0.7/0.3) | 557/1057 | 0.5270 | **-12** |

**BM25 带来负收益。** 加大 Dense 权重反而更差。

逐 query 分析（0.7/0.3 配置）：
- **BM25 更好**：4 条（+15 APIs）
- **Dense 更好**：11 条（+27 APIs）
- **相同**：85 条

BM25 有价值的场景：包含明确 API 名称（MJCF、Rasterizer）的查询，以及 Dense 完全失败的弱域（drone_medium 0→5）。

但 BM25 在更多查询上造成了退化，最严重的案例：

| 查询 ID | Dense 命中 | BM25 Hybrid 命中 | 退化 |
|---|---|---|---|
| s1_sph_fluid_complex_001 | 11/14 | 5/14 | **-6** |
| s1_drone_complex_002 | 6/14 | 3/14 | -3 |
| s1_drone_complex_003 | 6/15 | 3/15 | -3 |

### 2.3 失败根因分析

**核心问题：BM25 把 API 名称的层级结构打碎了。**

`genesis.morphs.Sphere` 被 BM25 拆成 `genesis`、`morphs`、`sphere` 三个独立 token。`genesis` 出现在几乎所有单元（无区分度），`morphs` 出现在几十个单元（低区分度），只有 `sphere` 有用。一个确定性很强的信号被稀释了。

知识单元的 `embedding_text` 包含完整 Python 代码，BM25 分词后 `Scene`、`build`、`Entity`、`add` 等高频 token 出现在绝大多数单元中，进一步加剧噪声。

例如 drone_complex 查询 "Build an urban obstacle course"，BM25 把 `build` 与所有包含 `Scene.build()` 的单元等价匹配，导致语义不相关的 `hover_env` 被推到 `fly` 前面。

**更关键的认识：我们根本不需要 BM25 来"发现"文档里有哪些 API。**

知识单元的 `all_apis` 元数据**已经明确列出了每一个 API**——如 `"genesis.Scene,genesis.options.morphs.MJCF,genesis.materials.Rigid,..."`. BM25 是在"不知道文档有什么"的前提下做模糊匹配，而我们已知信息，却还在用模糊方法。

---

## 三、方案 B：API Symbol Boost

### 3.1 设计思路

基于 BM25 失败的根因，我们提出**用结构化元数据做确定性匹配**替代 BM25 的概率匹配：

```
HyDE 伪代码 (search_query)
  │
  ├─ 正则提取 API 符号: [gs.morphs.Sphere, gs.materials.Rigid, ...]
  │     ↓
  │   resolve_api_to_known() → 标准化: [genesis.options.morphs.Sphere, ...]
  │
  └─ Dense 检索 → top-K 候选 (K > n_results)
                     │
                     └─ 对每个候选，计算符号重叠:
                          query_symbols ∩ candidate.all_apis
                            ↓
                        加权重排: (1-α) × dense_sim + α × overlap_ratio
                            ↓
                        返回 top n_results
```

### 3.2 与 BM25 的本质区别

| 维度 | BM25 | Symbol Boost |
|---|---|---|
| **匹配对象** | 文档全文打碎为 token | 仅匹配 `all_apis` 元数据中的 API ID |
| **匹配方式** | token 级模糊匹配（TF-IDF 加权） | 精确集合交集 |
| **噪声来源** | `genesis`/`morphs`/`build` 等通用 token | **零噪声**——只有已知 API ID 参与匹配 |
| **对 Dense 影响** | RRF 融合可能推翻 Dense rank 1 | 只做加分，不推翻 |
| **额外索引** | 需构建 BM25 索引（jieba 分词全部文档） | 无需额外索引，直接用已有元数据 |
| **回归风险** | 高（11 条查询退化） | **零（0 条查询退化）** |

### 3.3 实现细节

**符号提取（`SymbolMatcher.extract_symbols`）**：

1. 正则匹配 `gs.xxx.yyy(...)` / `genesis.xxx.yyy(...)` 模式
2. `gs` 前缀补全为 `genesis`（如 `gs.morphs.Sphere` → `genesis.morphs.Sphere`）
3. 复用已有 `api_id_normalize.py` 的 `resolve_api_to_known()` 映射到标准 API ID
4. 过滤未知 API，返回标准化列表

示例：
```
输入 (HyDE 伪代码):
  scene.add_entity(morph=gs.morphs.Sphere(), material=gs.materials.Rigid())

输出:
  [genesis.options.morphs.Sphere, genesis.materials.Rigid]
```

**加分重排（`SymbolMatcher.boost_rank`）**：

1. Dense 检索获取 top-K 候选（oversample 3×）
2. 对每个候选计算融合分数：
   - Dense 相似度归一化：`dense_sim = 1 - cosine_dist / 2`
   - 符号重叠率：`overlap = |query_symbols ∩ unit.all_apis| / |query_symbols|`
   - 最终分数：`score = (1-α) × dense_sim + α × overlap`（默认 α=0.3）
3. 按分数降序返回 top_n

关键设计：**如果查询中没有提取到 API 符号**（自然语言查询），直接返回原始 Dense 排序——Symbol Boost 只在有明确信号时介入，不会"帮倒忙"。

### 3.4 测试结果

相同 100 条 benchmark，相同评估标准。

| 配置 | 命中 APIs | Hit Rate | 差异 |
|---|---|---|---|
| 纯 Dense | 569/1057 | 0.5383 | baseline |
| BM25 + Dense (0.7/0.3) | 557/1057 | 0.5270 | -12 ❌ |
| **Symbol Boost (α=0.3)** | **576/1057** | **0.5449** | **+7 ✅** |

逐 query 分析：

| | Symbol Boost 更好 | Dense 更好 | 相同 |
|---|---|---|---|
| **查询数** | 2 | **0** | 98 |
| **净 API 变化** | +8 | 0 | — |

**Symbol Boost 实现了正向收益，且零回归。**

提升的 2 条查询：

| 查询 ID | 内容 | Dense 命中 | Boost 命中 | 提升 |
|---|---|---|---|---|
| s1_drone_medium_003 | Crazyflie 2.X 无人机控制 | 0/12 | **6/12** | **+6** |
| s1_terrain_complex_003 | 地形网格导入 | 4/12 | **5/12** | +1 |

`drone_medium_003` 的提升最为显著：Dense 完全没命中（0/12），Symbol Boost 通过匹配查询中的 `gs.morphs.Drone` 符号找到了包含该 API 的正确知识单元。这正是混合检索的设计目标——专有名词精确匹配。

---

## 四、三种方案对比总结

| 维度 | 纯 Dense | BM25 + Dense | **Symbol Boost** |
|---|---|---|---|
| Hit Rate | 0.5383 | 0.5270 (-12) | **0.5449 (+7)** |
| 退化的查询数 | — | 11 | **0** |
| 改善的查询数 | — | 4 | 2 |
| 净 API 变化 | — | -12 | **+7** |
| 额外开销 | 无 | BM25 索引构建 + 全文分词 | 无（直接用元数据） |
| 回归风险 | — | 高 | **无** |

---

## 五、分析

### 5.1 Symbol Boost 为什么有效

1. **精确而非模糊**：直接匹配 API ID 字符串，不经过分词，不丢失层级信息
2. **结构化而非统计**：利用已有的 `all_apis` 元数据，不需要从文档中"学习"关键词分布
3. **加分而非替代**：只给 Dense 候选加分，不引入新候选，不推翻已有排序
4. **有信号才介入**：自然语言查询提取不到符号时自动退化为纯 Dense

### 5.2 当前提升有限的原因

Symbol Boost 的效果受限于两个因素：

1. **查询中必须有 API 符号**。当前 benchmark 查询是自然语言（如 "Simulate a drone flying over terrain"），不含 `gs.morphs.Drone` 形式的符号。只有少量查询（如 `s1_drone_medium_003` 指定了 `gs.morphs.Drone(file=...)`) 含有可提取的符号。
2. **在实际 Agent 流水线中效果会更好**。Agent 使用 HyDE 模式——先让 LLM 生成伪代码骨架（含 `gs.morphs.Sphere()` 等调用），再用伪代码作为检索查询。HyDE 伪代码天然包含更多 API 符号，Symbol Boost 的提取率会显著高于直接用自然语言查询。

### 5.3 BM25 的保留价值

BM25 代码保留在 `hybrid_search.py` 中（`HybridSearch` + `HybridTokenizer` 类），未删除。当知识库规模增长（执行闭环持续积累新单元），BM25 的检索精度会随文档量增大而提高。建议在 300+ 知识单元后重新评估 BM25 效果。

---

## 六、文件结构

```
rag_demo/
├── hybrid_search.py          # 混合检索核心模块
│   ├── SymbolMatcher         # 方案 B：API 符号提取 + 候选重排（当前启用）
│   ├── HybridSearch          # 方案 A：BM25 索引 + RRF 融合（保留待用）
│   └── HybridTokenizer       # 中英混合分词器（BM25 专用）
├── rag_engine.py              # RAG 引擎（集成 Symbol Boost）
│   ├── _init_symbol_matcher  # 加载 known_apis 构建 SymbolMatcher
│   └── _symbol_boost_search  # Dense oversample → 符号重排
└── docs/
    └── hybrid_search_report.md  # 本报告
```

所有改动通过 `use_hybrid=True/False` 参数一键开关，`agent.py` 零改动。

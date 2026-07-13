# RAG vs No-RAG 对比实验报告

> **实验日期**: 2026-06-11
> **数据源**: `result.json`（同目录）
> **复跑脚本**: `benchmark/scripts/run_rag_vs_no_rag.py`

---

## 1. 实验目的

量化 **RAG 检索对 Genesis 代码生成 Agent 的执行成功率贡献**。对比两种条件：

| 组别 | 配置 | 说明 |
|---|---|---|
| **A) No RAG** | `knowledge_list=[]` | 完全不给 LLM 任何检索上下文，纯靠 DeepSeek-R1 的训练知识生成 |
| **B) Best RAG** | hyde + unit + rerank(top_n=10) + SymbolMatcher + 满配检索量 | 当前 RAG 系统的最豪华配置 |

两组都**启用代码执行**（非 `--no-exec`），评测真实可运行性。

---

## 2. 实验设置

- **任务集**: 10 个任务（4 simple + 3 medium + 3 hard），从 `benchmark/query.json` 选取代表性子集
- **LLM**: DeepSeek-R1 (`deepseek-reasoner`)
- **最大重试**: 3 次（对应 Pass@1 / Pass@3）
- **执行超时**: 600 秒/次
- **执行环境**: `GENESIS_OFFSCREEN=1`（无头模式）

**Best RAG 检索参数**:

```python
{
    "rewrite_mode": "hyde",          # HyDE 查询重写
    "hyde_route": "unit",            # 知识单元检索路由
    "n_api": 10, "n_code": 3, "n_snippet": 5, "n_units": 10,  # 满配检索量
    "rerank": True, "rerank_top_n": 10, "rerank_oversample": 2.0,  # 交叉编码器重排
    "use_hybrid": True,              # SymbolMatcher 符号增强混合检索
    "include_core_api": True, "core_api_limit": 40,
}
```

---

## 3. 核心结论

| 指标 | No RAG | Best RAG | 提升 |
|---|---|---|---|
| **Pass@1** | **10%** (1/10) | **60%** (6/10) | **+50pp（6 倍）** |
| **Pass@3** | **30%** (3/10) | **80%** (8/10) | **+50pp（2.7 倍）** |
| 成功任务的平均尝试次数 | 2.0 次 | 1.375 次 | — |

**RAG 的价值非常显著**：Pass@1 提升 6 倍，Pass@3 提升 2.7 倍。No RAG 条件下，纯靠 LLM 训练知识几乎无法生成可直接运行的 Genesis 代码。

---

## 4. 逐任务结果

| # | Task | 复杂度 | Query | No RAG (P@1/P@3) | Best RAG (P@1/P@3) |
|---|---|---|---|---|---|
| 1 | eval_001 | simple | 红色刚体球自由落体到地面 | ❌ / ❌ | ✅ / ✅ |
| 2 | eval_002 | simple | 静态刚体盒子作障碍物 | ❌ / ❌ | ❌ / ✅ |
| 3 | eval_003 | simple | 刚体圆柱从 3 米落下 | ❌ / ✅ | ✅ / ✅ |
| 4 | eval_004 | simple | 零重力环境下的刚体盒子 | ❌ / ❌ | ✅ / ✅ |
| 5 | eval_006 | medium | 两球并排落到地面 | ✅ / ✅ | ✅ / ✅ |
| 6 | eval_007 | medium | 三个盒子竖直堆叠 | ❌ / ✅ | ✅ / ✅ |
| 7 | eval_008 | medium | 小球落到大盒子中心 | ❌ / ❌ | ❌ / ✅ |
| 8 | eval_016 | hard | 兔子网格软体弹性体落地 | ❌ / ❌ | ❌ / ❌ |
| 9 | eval_017 | hard | Franka 机械臂 + 红盒子 | ❌ / ❌ | ✅ / ✅ |
| 10 | eval_018 | hard | 浴缸网格作静态刚体容器 | ❌ / ❌ | ❌ / ❌ |

---

## 5. 按复杂度分层

### No RAG

| 复杂度 | N | Pass@1 | Pass@3 |
|---|---|---|---|
| simple | 4 | 0/4 (0%) | 1/4 (25%) |
| medium | 3 | 1/3 (33%) | 2/3 (67%) |
| hard | 3 | 0/3 (0%) | 0/3 (0%) |

### Best RAG

| 复杂度 | N | Pass@1 | Pass@3 |
|---|---|---|---|
| simple | 4 | 3/4 (75%) | 4/4 (100%) |
| medium | 3 | 2/3 (67%) | 3/3 (100%) |
| hard | 3 | 1/3 (33%) | 1/3 (33%) |

**观察**：
- RAG 在 **simple/medium 任务上效果最显著**——No RAG 在 simple 上几乎全军覆没，加 RAG 后 Pass@3 达 100%。
- **Hard 任务仍是难点**：即使有 RAG，3 个 hard 任务中也只有 1 个（Franka 机械臂）成功。eval_016（软体兔子）和 eval_018（浴缸容器）两种配置全部失败。

---

## 6. 关键发现

1. **No RAG 基本不可用**——10 个任务里只有 eval_006（两球碰撞）一次通过，说明 DeepSeek-R1 的训练数据对 Genesis 的 API 细节（`gs.morphs.*`、`gs.Scene` 生命周期、材质/表面枚举）覆盖极差。

2. **RAG 不仅提高成功率，还减少重试次数**——Best RAG 成功任务平均 1.375 次通过（多为第 1 次就成），No RAG 成功任务平均需 2 次。说明检索上下文让 LLM 第一次就能写出正确结构。

3. **RAG 在 hard 任务上收益有限**——软体网格变形（eval_016）和复杂容器几何（eval_018）可能需要更精细的检索策略（如 mesh 处理专属知识单元）或执行反馈闭环，单纯堆检索量不足以解决。

4. **时间成本**——Best RAG 总耗时 1154s vs No RAG 896s（多约 29%），主要来自 HyDE 重写 + 重排 + 更大检索量。但考虑到成功率翻倍，这个时间成本完全划算。

---

## 7. 复跑方法

```bash
cd rag_demo/
python -u benchmark/scripts/run_rag_vs_no_rag.py
```

脚本会自动跑全部 10 个任务的两组对比，输出汇总表，并保存 JSON 结果。任务集和 RAG 参数可在脚本顶部的 `TASK_IDS` 和 `BEST_RAG_PARAMS` 常量中调整。

---

## 8. 后续建议

- **扩大样本**：10 个任务的结论方向清晰，但 hard 任务样本太少（3 个），建议补到 8~10 个再下定论。
- **失败任务归因**：eval_016/eval_018 即使有 RAG 也失败，值得单独看是检索没召回、还是召回了但 LLM 仍写错（可查 `result.json` 里对应 task 的 `attempts[].error`）。
- **与 `newest/` 批量结果交叉验证**：`results/newest/` 有 8 组 RAG 配置的网格搜索，可对比不同 rerank top_n 的边际收益。

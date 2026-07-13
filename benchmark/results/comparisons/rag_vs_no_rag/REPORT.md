# RAG vs No-RAG 对比实验报告

> **实验日期**: 2026-06-16
> **Base Model**: `deepseek-v4-pro`（修正自 `.env` 配置；首次实验误用了 `deepseek-reasoner`，已修正并复跑）
> **数据源**: `result.json`（同目录，v4-pro 结果）
> **R1 对照数据**: `result_R1.json`（同目录，首次实验的 R1 结果，留存对比）
> **复跑脚本**: `benchmark/scripts/run_rag_vs_no_rag.py`

---

## 1. 实验目的

量化 **RAG 检索对 Genesis 代码生成 Agent 的执行成功率贡献**。对比两种条件：

| 组别 | 配置 | 说明 |
|---|---|---|
| **A) No RAG** | `knowledge_list=[]` | 完全不给 LLM 任何检索上下文，纯靠模型自身能力生成 |
| **B) Best RAG** | hyde + unit + rerank(top_n=10) + SymbolMatcher + 满配检索量 | 当前 RAG 系统的最豪华配置 |

两组都**启用代码执行**（非 `--no-exec`），评测真实可运行性。

---

## 2. 实验设置

- **任务集**: 10 个任务（4 simple + 3 medium + 3 hard），从 `benchmark/query.json` 选取代表性子集
- **Base Model**: `deepseek-v4-pro`（DeepSeek API）
- **最大重试**: 3 次（对应 Pass@1 / Pass@3）
- **执行超时**: 600 秒/次
- **执行环境**: `GENESIS_OFFSCREEN=1`（无头模式），conda 环境 `env_genesis`

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

> **修复说明**: 首次实验时 `agent.py` 硬编码了 `model="deepseek-reasoner"`，未读 `.env` 中的 `DEEPSEEK_MODEL="deepseek-v4-pro"`。已修复为读环境变量（见 `agent.py` 顶部 `DEEPSEEK_MODEL` 与 `GenesisAgent.__init__`）。本报告所有数据均为修复后、使用 v4-pro 的复跑结果。

---

## 3. 核心结论（deepseek-v4-pro）

| 指标 | No RAG | Best RAG | 提升 |
|---|---|---|---|
| **Pass@1** | **20%** (2/10) | **70%** (7/10) | **+50pp（3.5 倍）** |
| **Pass@3** | **30%** (3/10) | **80%** (8/10) | **+50pp（2.7 倍）** |
| 成功任务的平均尝试次数 | 1.67 次 | 1.13 次 | — |

**RAG 的价值依然非常显著**：Pass@1 从 20% 提升到 70%，Pass@3 从 30% 提升到 80%。No RAG 条件下，大部分任务无法生成可直接运行的 Genesis 代码。

---

## 4. 逐任务结果（deepseek-v4-pro）

| # | Task | 复杂度 | Query | No RAG (P@1/P@3) | Best RAG (P@1/P@3) |
|---|---|---|---|---|---|
| 1 | eval_001 | simple | 红色刚体球自由落体到地面 | ✅ / ✅ | ❌ / ✅ |
| 2 | eval_002 | simple | 静态刚体盒子作障碍物 | ❌ / ❌ | ✅ / ✅ |
| 3 | eval_003 | simple | 刚体圆柱从 3 米落下 | ❌ / ❌ | ✅ / ✅ |
| 4 | eval_004 | simple | 零重力环境下的刚体盒子 | ❌ / ❌ | ✅ / ✅ |
| 5 | eval_006 | medium | 两球并排落到地面 | ✅ / ✅ | ✅ / ✅ |
| 6 | eval_007 | medium | 三个盒子竖直堆叠 | ❌ / ✅ | ✅ / ✅ |
| 7 | eval_008 | medium | 小球落到大盒子中心 | ❌ / ❌ | ✅ / ✅ |
| 8 | eval_016 | hard | 兔子网格软体弹性体落地 | ❌ / ❌ | ❌ / ❌ |
| 9 | eval_017 | hard | Franka 机械臂 + 红盒子 | ❌ / ❌ | ✅ / ✅ |
| 10 | eval_018 | hard | 浴缸网格作静态刚体容器 | ❌ / ❌ | ❌ / ❌ |

> **注**: eval_001 是唯一一个 No RAG 反而比 Best RAG 强的任务（No RAG 一次通过，Best RAG 首次失败第二次成功）。极简任务上，v4-pro 凭自身能力即可，RAG 上下文偶尔反而干扰了首版生成。

---

## 5. 按复杂度分层

### No RAG

| 复杂度 | N | Pass@1 | Pass@3 |
|---|---|---|---|
| simple | 4 | 1/4 (25%) | 1/4 (25%) |
| medium | 3 | 1/3 (33%) | 2/3 (67%) |
| hard | 3 | 0/3 (0%) | 0/3 (0%) |

### Best RAG

| 复杂度 | N | Pass@1 | Pass@3 |
|---|---|---|---|
| simple | 4 | 3/4 (75%) | 4/4 (100%) |
| medium | 3 | 3/3 (100%) | 3/3 (100%) |
| hard | 3 | 1/3 (33%) | 1/3 (33%) |

**观察**：
- RAG 在 **simple/medium 任务上效果最显著**——加 RAG 后 Pass@3 达 100%。
- **Hard 任务仍是难点**：即使有 RAG，3 个 hard 任务中也只有 1 个（Franka 机械臂）成功。软体网格变形（eval_016）和复杂容器几何（eval_018）两种配置全部失败。

---

## 6. 与首次 R1 实验的对比

首次实验误用 `deepseek-reasoner`（R1），已修正。两版结果对比：

| 指标 | R1 No RAG | R1 Best RAG | v4-pro No RAG | v4-pro Best RAG |
|---|---|---|---|---|
| **Pass@1** | 10% (1/10) | 60% (6/10) | 20% (2/10) | **70% (7/10)** |
| **Pass@3** | 30% (3/10) | 80% (8/10) | 30% (3/10) | 80% (8/10) |
| 成功平均尝试次数 | 2.00 | 1.375 | 1.67 | **1.125** |
| 总耗时 | 896s | 1154s | 1652s | 2132s |

**跨模型观察**：
1. **v4-pro 的 No RAG 基线更强**——P@1 从 10%→20%，说明 v4-pro 自身对 Genesis API 的掌握比 R1 更好。
2. **v4-pro + RAG 的 Pass@1 最高（70%）**，且成功任务平均只需 1.13 次尝试（最稳）。
3. **两个模型的 Pass@3 上限一致（80%）**——RAG 把成功率天花板顶到 8/10，剩下 2 个 hard 任务（eval_016 软体、eval_018 浴缸）是 RAG 当前也解决不了的。
4. **v4-pro 更慢**——总耗时约为 R1 的 1.8 倍，可能因生成更长的推理/代码。

---

## 7. 关键发现

1. **No RAG 基本不可用**——即使 v4-pro 比 R1 强，No RAG 的 Pass@1 也只有 20%，说明 Genesis API 细节（`gs.morphs.*`、`gs.Scene` 生命周期、材质/表面枚举）超出通用 LLM 训练覆盖范围。

2. **RAG 不仅提高成功率，还显著减少重试次数**——Best RAG 成功任务平均 1.13 次通过（多为第 1 次就成），No RAG 成功任务平均需 1.67 次。检索上下文让 LLM 第一次就能写出正确结构。

3. **RAG 在 hard 任务上收益有限**——软体网格变形（eval_016）和复杂容器几何（eval_018）可能需要更精细的检索策略（如 mesh 处理专属知识单元）或执行反馈闭环，单纯堆检索量不足以解决。

4. **极简任务上 RAG 偶有反效果**——eval_001 上 No RAG 一次通过、Best RAG 首次失败。这类任务模型自身能力足够，过量的检索上下文偶尔干扰首版生成。

5. **时间成本**——Best RAG 总耗时 2132s vs No RAG 1652s（多约 29%），主要来自 HyDE 重写 + 重排 + 更大检索量。考虑到 Pass@1 提升 3.5 倍，这个时间成本完全划算。

---

## 8. 复跑方法

```bash
cd rag_demo/
conda activate env_genesis          # 需含 openai、genesis 等依赖
python -u benchmark/scripts/run_rag_vs_no_rag.py
```

脚本会自动跑全部 10 个任务的两组对比，输出汇总表，并保存 JSON 结果（含 `model` 字段）。任务集和 RAG 参数可在脚本顶部的 `TASK_IDS` 和 `BEST_RAG_PARAMS` 常量中调整。模型由 `DEEPSEEK_MODEL` 环境变量控制（`.env` 中为 `deepseek-v4-pro`）。

---

## 9. 后续建议

- **扩大样本**：10 个任务结论方向清晰，但 hard 任务样本太少（3 个），建议补到 8~10 个再下定论。
- **失败任务归因**：eval_016/eval_018 即使有 RAG 也失败，值得单独看是检索没召回、还是召回了但 LLM 仍写错（查 `result.json` 里对应 task 的 `attempts[].error`）。
- **极简任务的反效果排查**：eval_001 上 RAG 反而首次失败，值得对比 RAG 给出的上下文是否引入了与任务无关的噪声。
- **与 `newest/` 批量结果交叉验证**：`results/newest/` 有 8 组 RAG 配置的网格搜索，可对比不同 rerank top_n 的边际收益。

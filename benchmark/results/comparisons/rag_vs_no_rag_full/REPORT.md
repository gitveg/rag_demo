# RAG vs No-RAG 全量对比实验报告（100 条）

> **实验日期**: 2026-06-17 ~ 2026-06-18（中途死机一次，断点续跑完成）
> **Base Model**: `deepseek-v4-pro`
> **任务规模**: query.json 全量 100 条
> **数据源**: `result.json`（执行+召回合并）· `result.exec_only.json`（原始执行备份）
> **可视化**: `report.html`（同目录）
> **召回数据来源**: `newest/08_hyde_unit_rerank-10`（no-exec 召回跑批，复用未重跑）

---

## 0. 一句话结论

> **RAG 召回率 91%（93% 任务召回充分），但 Pass@1 仅 43%——瓶颈在生成质量（属性/参数幻觉），不在检索。**
> 干净重跑确认：LLM 召回对了 API 名字，却编造了不存在的属性（`Unrecognized attribute`）、方法（`has no attribute`）、资产路径。
> **Best RAG Pass@1=43% Pass@3=65%**（vs No RAG 11%/28%），RAG 提升 ~4 倍但绝对成功率仍有很大空间。

> ✅ **锁 bug 已修复并验证**：Taichi 缓存锁污染从 145 次降至 7 次（-95%）。详见 §0.1。

---

## 0.1 执行环境污染与抽样验证 ⚠️（汇报必读）

本次跑批发现并定位了一个**执行环境 bug**，对结论有重要影响，如实记录：

### Bug：Taichi kernel 编译缓存僵尸锁

- **现象**：149 个失败 attempt 中 **145 个（97%）报 `ticache.lock failed`**，而非真实代码错误。
- **根因**：`C:/gstaichi_cache/.../ticache.lock` 是个 0 字节僵尸锁，超时/崩溃的子进程残留；执行函数从不清它。**需要编译新 kernel 的任务（相机/传感器/复杂场景）撞锁即死，3 次重试全挂；kernel 已预编译的任务（简单刚体）不受影响、照常通过。**
- **影响范围**：No RAG 77/85 失败、Best RAG 38/40 失败是纯环境锁死。→ **本次 Pass@k 数字是污染后的下限，不可直接当作真实成功率。**
- **已修复**：执行函数现在每次执行前删僵尸锁（`run_rag_vs_no_rag.py: _clean_ti_lock`）。

### 抽样验证：删锁后重跑，揭示真实失败模式

清除僵尸锁后，对 11 个"纯环境锁死"任务重跑其生成代码——**11 个仍全部失败**，挖出真实错误：

| 失败模式 | 示例 | 频次 |
|---|---|---|
| **属性/参数幻觉** | `Unrecognized attribute: solver`、`'DroneEntity' has no attribute 'mass'`、`Unrecognized attribute: pos` | **主导** |
| **方法幻觉** | `'Tensor' object has no attribute 'copy'` | 常见 |
| **资产路径幻觉** | `File not found: 'meshes/bathtub.obj'` | 偶发 |
| **数据格式错** | numpy 数组形状错误 (inhomogeneous shape) | 偶发 |

### 结论修正

1. **"生成是瓶颈"的结论成立且更强了**——锁 bug 只是**掩盖**了真实错误，删锁后真实错误暴露，主导模式正是属性/参数幻觉。
2. **召回率 91% 但生成常因属性幻觉失败**——LLM 召回对了 API 名字，却编造了不存在的属性/方法。这正是生成质量问题。
3. **本次 Pass@k（60%）是受污染下限**，真实值需干净重跑（已修 bug，可重跑验证）。
4. **最可操作的改进点**：给知识库补 **API 属性白名单**（让 LLM 知道哪些属性合法），生成时加强属性校验——直击属性幻觉。

---

## 1. 实验目的与设置

对比 **No RAG**（纯 LLM）与 **Best RAG**（满配检索）在 Genesis 代码生成上的**真实执行成功率**，并结合召回率做**召回 ↔ 生成关联分析**，定位系统瓶颈。

| 项目 | 配置 |
|---|---|
| 任务集 | query.json 全量 100 条（31 simple + 40 medium + 29 hard） |
| Base Model | `deepseek-v4-pro`（DeepSeek API） |
| 执行 | 启用（非 `--no-exec`），`GENESIS_OFFSCREEN=1` |
| 最大重试 | 3 次（Pass@1 / Pass@3） |
| 执行超时 | 600 秒/次 |
| 环境 | conda `env_genesis` |
| 总耗时 | ~11.9 小时（含一次死机续跑） |

**Best RAG 检索参数（执行跑批实际使用）**:

```python
{
    "rewrite_mode": "hyde", "hyde_route": "unit",
    "n_api": 10, "n_code": 3, "n_snippet": 5, "n_units": 10,  # 满配
    "rerank": True, "rerank_top_n": 10, "rerank_oversample": 2.0,
    "use_hybrid": True,  # SymbolMatcher
    "include_core_api": True, "core_api_limit": 40,
}
```

---

## 2. 总体结果（100 条）

| 指标 | No RAG | Best RAG | 提升 |
|---|---|---|---|
| **Pass@1** | 11/100 (11%) | **43/100 (43%)** | +32pp（~4 倍）|
| **Pass@3** | 28/100 (28%) | **65/100 (65%)** | +37pp（~2.3 倍）|
| RAG 召回率 | —（无检索） | 90.9% | — |
| 语义召回率 | — | 86.6% | — |

> ✅ **数字为干净重跑结果**（锁 bug 已修复，锁残余 7/125=5.6%）。与污染版（8%/15% vs 39%/60%）对比，No RAG 从 8→11%、Best RAG 从 39→43%，锁污染低估了 3-4pp，方向不变。

> **RAG 价值依然显著**：Pass@1 从 11% 提升到 43%（~4 倍），Pass@3 从 28% 提升到 65%（~2.3 倍）。绝对值较早期 10 条子集（70%/80%）大幅修正，全量才是真实水平（见 §6）。

---

## 3. 按复杂度分层

| 复杂度 | N | No RAG (P@1 / P@3) | Best RAG (P@1 / P@3) |
|---|---|---|---|
| simple | 31 | 19% / 39% | **61% / 87%** |
| medium | 40 | 10% / 28% | **48% / 65%** |
| hard | 29 | 3% / 17% | **17% / 41%** |

RAG 在所有难度上都有显著拉动，但难度越高绝对成功率越低。simple 的 Pass@3 达 87%，hard 仅 41%。

---

## 4. 按领域分层（Best RAG）⭐

按 task_id 前缀拆分的领域表现，**最能定位问题在哪**：

| 领域 | N | 召回率 | P@1 | P@3 | 诊断 |
|---|---|---|---|---|---|
| rigid_basics | 20 | 99% | 65% | 90% | ✅ 表现好 |
| fem_cloth | 3 | 100% | 67% | 67% | ⚠️ 生成不稳 |
| fem_elastic | 7 | 98% | 71% | 71% | ✅ 表现好 |
| sph_fluid | 9 | 97% | 44% | 78% | ✅ 表现好 |
| mpm_sand | 4 | 96% | 50% | 100% | ✅ |
| **camera** | 5 | 96% | **0%** | 20% | 🔴 召回满却几乎全败 |
| robot | 8 | 95% | 38% | 62% | ⚠️ 生成不稳 |
| force_field | 8 | 92% | 38% | 62% | ⚠️ 生成不稳 |
| surface | 8 | 91% | 62% | 75% | ✅ |
| cross_domain | 7 | 81% | 14% | 43% | ⚠️ 生成瓶颈 |
| terrain | 7 | 77% | 43% | 71% | ⚠️ 检索不足 |
| **sensor** | 6 | 77% | **0%** | **0%** | ⚠️ 生成瓶颈 |
| drone | 8 | 76% | 25% | 50% | ⚠️ 检索不足 |

**关键观察**：
- **camera / sensor 仍然是最难领域**：camera 召回 96% 却 P@1=0%（生成的代码完全跑不起来）；sensor 召回仅 77% 且 P@1=0%。这些领域的 API 用法（相机参数、传感器配置）即使召回到也组装不对，是优先攻关对象。
- **rigid_basics（刚体基础）是主力且表现最稳**（20 条，P@3=90%）——RAG 对常见刚体场景已经相当成熟。
- **terrain 和 drone 检索召回偏低（76-77%）**，但生成成功率并非最差，说明即使召回不足，简单场景下 LLM 仍能拼凑出可运行代码。
- **fem_elastic / sph_fluid / mpm_sand / surface 相比污染版大幅提升**——证明了锁 bug 修复后，以前被锁死的任务很多是可以跑通的。

---

## 5. 召回 ↔ 生成关联分析 ⭐⭐

（本节基于干净重跑数据 + 重新合并召回率，已排除锁污染）

### 5.1 四象限分布（召回阈值 0.7，按 Pass@1）

| 象限 | 数量 | 占比 | 含义 |
|---|---|---|---|
| ✅ 高召回 + P@1 成功 | 42 | 42% | RAG 完美发挥 |
| ⚠️ **高召回 + P@1 失败** | **51** | **51%** | **召回到了，生成没用好** |
| 🤔 低召回 + P@1 成功 | 1 | 1% | 侥幸成功 |
| ❌ 低召回 + P@1 失败 | 6 | 6% | 真正的检索缺口 |

### 5.2 按召回率分桶的执行成功率

| 桶 | N | 平均召回 | P@1 | P@3 |
|---|---|---|---|---|
| 高召回（≥0.7） | 93 | 93% | 45% | 69% |
| 低召回（<0.7） | 7 | 67% | 14% | 14% |

### 5.3 核心结论

**检索不是瓶颈。** 93% 的任务召回了 ≥70% 的正确 API，但高召回任务里只有 45% 能 Pass@1。

**真正的瓶颈是代码生成与执行：**
- **51 个"高召回却失败"的任务**占失败的绝大多数。这些任务的 API 文档已经喂给 LLM，但生成的代码组装不对（属性/参数幻觉主导）。
- 真正因"检索不足"导致失败的只有 **6 个**（力场/地形/无人机/传感器/跨域）。
- **clean 数据比污染版更明确了这个结论**：四象限分布几乎没有变化（51 vs 旧 55），方向稳固。

**改进方向：**
1. **生成质量**：高召回任务的属性/参数幻觉是头号问题（详见 §0.1 验证）。
2. **执行反馈闭环**：当前重试盲目（Pass@3 仅比 P@1 多 22pp）。接入报错反馈可让每次重试更有针对性。
3. **检索查漏补缺**：drone / terrain / cross_domain / sensor 的召回偏低，需补强知识库。

### 5.4 典型任务清单

**高召回却失败（生成瓶颈，51 个，节选）**:
`eval_001` · `eval_016` · `eval_011` · `s1_sph_fluid_*` · `s1_mpm_sand_*` · `s1_surface_*` · `s1_fem_cloth_medium_003`

**低召回且失败（检索瓶颈，6 个）**:
`s1_terrain_complex_003` · `s1_force_field_complex_001` · `s1_drone_medium_002` · `s1_drone_complex_002` · `s1_sensor_simple_001` · `s1_cross_domain_complex_006`

---

## 6. 与 10 条子集的对比（重要修正）

| | 10 条代表性子集 | **100 条全量（干净）** |
|---|---|---|
| Best RAG Pass@1 | 70% | **43%** |
| Best RAG Pass@3 | 80% | **65%** |

⚠️ **10 条子集严重高估了系统能力**——它偏向选了刚体/碰撞这类常见且 RAG 表现好的任务。**全量结论应以本报告的 43%/65% 为准。**

---

## 7. 关键发现汇总

1. **RAG 把 Pass@1 从 11% 拉到 43%（4 倍），Pass@3 从 28% 拉到 65%（~2.3 倍）**——RAG 对 Genesis 代码生成是刚需。
2. **召回率 91%、生成成功率 65%（P@3）——瓶颈在生成不在检索。** 93% 的任务召回充分，但高召回任务中只有 45% 能 Pass@1，51% 因代码质量问题失败。
3. **领域分化严重**：rigid_basics 表现最稳（P@3=90%）；camera/sensor 仍是送命题（camera 召回 96% 却 P@1=0%；sensor 召回 77% 且 P@1=0%）。
4. **10 条子集高估了 ~27pp**，全量才是真实水平。
5. **锁 bug 修复确认**：干净重跑后锁残余 7/125=5.6%（vs 之前 145/149=97%）。camera/sensor 等复杂任务现在能跑到真实错误而非锁死。
6. **Pass@3 比 Pass@1 高 22pp**（43%→65%），重试有一定收益，但接入报错反馈闭环后可让每次重试更有针对性。

---

## 8. 方法论说明与数据口径

- **召回率口径**：来自 `newest/08_hyde_unit_rerank-10`（no-exec 召回跑批），按 task_id 合并。它的检索量（n_api=6/n_units=5）小于执行跑批的满配（10/10），因两者最终都 rerank 到 top-10，故**召回率为保守近似**——真实召回可能略高。合并脚本 `benchmark/scripts/merge_recall.py`，原执行数据备份在 `result.exec_only.json`。
- **复杂度命名**：query.json 中 `complex` 与 `hard` 指同一难度，本报告统一为 hard。
- **断点续跑**：实验中遇一次死机，已完成的 35 条增量落盘未丢失，续跑完成。
- **执行判定**：`returncode == 0` 视为成功；超时（600s）或异常视为失败。

---

## 9. 文件索引与复现

```
benchmark/results/comparisons/rag_vs_no_rag_full/
├── REPORT.md              ← 本报告
├── result.json            ← 执行 + 召回（合并后，含 recall_source 说明）
├── result.exec_only.json  ← 原始执行数据备份（未含召回）
└── report.html            ← 交互式可视化（含召回列、对比柱状图、逐任务热力表）
```

**复现命令**:

```bash
cd rag_demo/
conda activate env_genesis

# 1. 全量执行对比（断点续跑，可中断重跑）
python -u benchmark/scripts/run_rag_vs_no_rag.py --all

# 2. 合并召回率（复用 newest/08，无需重跑检索）
python benchmark/scripts/merge_recall.py \
    --exec benchmark/results/comparisons/rag_vs_no_rag_full/result.json

# 3. 生成可视化
python benchmark/scripts/viz_comparison.py \
    benchmark/results/comparisons/rag_vs_no_rag_full/result.json
```

---

## 10. 后续建议（按优先级）

| 优先级 | 方向 | 预期收益 |
|---|---|---|
| 🔴 高 | **补 API 属性白名单 + 生成时属性校验**（直击属性幻觉，§0.1 验证的主导失败模式） | 直接修复最常见的 `Unrecognized attribute` / `has no attribute` 错误 |
| 🔴 高 | **用修好的执行函数干净重跑污染任务**（锁 bug 已修，38 best_rag + 77 no_rag） | 得到可信真实 Pass@k + 完整错误分布 |
| 🔴 高 | **接入执行反馈闭环**（失败后把真实报错喂回 LLM） | 当前盲目重试浪费大；现在能拿到真实错误（属性名等），反馈更有针对性 |
| 🟡 中 | **补强 drone/terrain/cross_domain/sensor 知识库** | 解决检索召回率偏低的领域 |
| 🟢 低 | 跑满配检索的精确召回（替换 newest/08 近似值） | 仅修正 ~1-2pp 召回口径 |

> ✅ **已完成**：定位并修复 Taichi 缓存锁僵尸 bug（`_clean_ti_lock`）。

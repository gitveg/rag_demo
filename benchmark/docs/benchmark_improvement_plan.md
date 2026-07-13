# Benchmark 系统优化完善方案

> 日期：2026-06-11
> 状态：进行中（P0.1 ✅、P1.1 ✅ 已完成）

---

## 一、现状概览

当前 benchmark 已具备的能力：

| 能力 | 状态 | 说明 |
|------|------|------|
| 评测 query 集 | ✅ 已有 | 77 条任务，14 个 domain，3 档复杂度 |
| RAG hit rate 计算 | ✅ 已有 | 语义检索 vs Core API 注入 vs 未命中，三分类 |
| 查询重写对比 | ✅ 已有 | none / translate / hyde，三种 rewrite mode |
| HyDE 路由对比 | ✅ 已有 | unit / fourway，两种路由路径 |
| 批量运行 | ✅ 已有 | `run_benchmark_batch.py`，串行执行多组实验 |
| HTML 可视化 | ✅ 已有 | Chart.js 条形图 + heatmap，单次 & 多次对比 |
| Miss KB 审计 | ✅ 已有 | 区分"KB 中不存在" vs "存在但未检索到" |
| 查询代码生成 | ✅ 已有 | `query_gen.py`，GPT-5.4 生成 + AST 提取 API |

当前 benchmark 存在的问题：

| 问题 | 严重程度 | 说明 |
|------|----------|------|
| Reranker 是空壳 | ✅ 已完成 | 已接入 `rag_engine.py`，`--rerank` 参数生效 |
| 执行评测从未运行 | 🔴 高 | 所有 batch 都是 `--no-exec`，Pass@1/3 永远 null |
| Incremental RAG 指标未激活 | 🟡 中 | 函数已实现，pipeline 不调用 |
| Complexity 命名不一致 | ✅ 已完成 | `metrics.py` 中统一 `"complex" → "hard"` 映射 |
| Batch 配置硬编码 | 🟡 中 | 改实验要改源码 |
| rag_adapter 紧耦合 | 🟡 中 | 直接调用 agent 私有方法 |
| 缺 domain 维度统计 | 🟢 低 | 只有 complexity 分组，无 domain 分组 |
| 无历史趋势图 | 🟢 低 | 10+ 次运行无法跨时间对比 |
| 无 token 效率指标 | 🟢 低 | 有 token 数和 hit rate，无性价比指标 |
| Miss audit 未集成到 HTML | 🟢 低 | 独立 markdown，不在可视化中 |
| Retry 不用错误反馈 | ⚪ 可选 | 每次 retry 从零生成，不利用执行错误 |
| 无参数网格搜索 | ⚪ 可选 | 只测 rewrite 组合，未做参数消融 |
| Feedback Loop 未打通 | ⚪ 可选 | benchmark 与 feedback 完全独立 |

---

## 二、P0 — 激活已有但未使用的功能

### 2.1 接入 Reranker 到 RAG search 流水线 ✅ 已完成

**现状**：

- `reranker.py` 已实现完整的 `Reranker` 类：
  - `rerank_by_groups(items, groups_top_n)` — 按类型分组重排，支持每类指定保留数量
  - 使用 DashScope `gte-rerank` 模型做 cross-encoder 重排序
  - 支持 fallback（API 失败时退回原始排序）
- 但 `rag_engine.py:791` 中 `search()` 方法遇到 `rerank=True` 时只打印 warning 然后 skip：
  ```python
  if rerank:
      print("[RAG] ⚠ rerank not implemented in rag_demo, skipped")
  ```
- benchmark CLI 的 `--rerank` 和 `--rerank-top-n` 参数传入后无实际效果

**改动方案**：

1. **`rag_engine.py` — 在 `search()` 末尾接入 reranker**：
   - 在四路检索（fourway path）和 unit path 的结果合并后、返回前，插入 rerank 步骤
   - 当 `rerank=True` 时：
     - 将所有检索到的 items（API docs + code + snippets + units）扁平化为统一列表
     - 调用 `Reranker.rerank_by_groups(items, groups_top_n)`，其中 `groups_top_n` 由 `rerank_top_n` 参数决定
     - 用重排后的结果替换原始结果
   - 保留 `rerank_oversample` 逻辑：检索时按 oversample 倍数多取，rerank 后截断

2. **`benchmark/pipeline.py` — 确保参数透传**：
   - 验证 `rerank` 和 `rerank_top_n` 正确传递到 `GenesisRAG.search()`

3. **`run_benchmark_batch.py` — 新增 rerank 实验组**：
   - 在 COMMANDS 中加入 `--rerank --rerank-top-n 10` 的配置

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `rag_engine.py` | `search()` 方法中接入 `Reranker.rerank_by_groups()` |
| `benchmark/pipeline.py` | 确认 rerank 参数透传（可能已正确，需验证） |
| `benchmark/run_benchmark_batch.py` | 新增 rerank 实验组 |
| `benchmark/run_benchmark.py` | 无需改动（已支持 `--rerank`） |

**验证**：

```bash
conda activate env_genesis
python -m benchmark.run_benchmark --no-exec --rewrite-mode hyde --rerank --rerank-top-n 10 --tasks s1_robot_simple_001,s1_sph_fluid_simple_001
```

确认输出中有 rerank 相关日志，且 JSON 结果中 `rerank: true` 被记录。

> **已完成（2026-06-11）**：在 `rag_engine.py` 中新增 `_apply_rerank()` 方法，在 unit 路径和 fourway 路径的 `return out` 前调用 `Reranker.rerank()`。失败时静默 fallback，不影响主流程。batch 实验组可后续按需添加。

---

### 2.2 激活执行评测（Pass@1/Pass@3）

**现状**：

- `pipeline.py` 中 `_run_task()` 的完整执行路径已实现：
  1. RAG 检索 → 获取 context
  2. 循环 `max_retries` 次（默认 3）：调用 `agent.solve()` 生成代码 → `_execute_generated_code()` 执行
  3. 记录每次 attempt 的 success/failure
  4. 计算 Pass@1、Pass@3
- `_execute_generated_code()` 已处理超时（600s）、异常捕获、环境变量注入（`GENESIS_OFFSCREEN=1`）
- 但所有 batch run 都用 `--no-exec`，从未真正执行过生成的代码
- `viz_report.py` 已有 Pass@1/Pass@3 的渲染逻辑，当值为 null 时显示 "N/A"

**改动方案**：

1. **`run_benchmark_batch.py` — 新增执行评测实验组**：
   - 在 COMMANDS 中增加不带 `--no-exec` 的配置（只跑 `simple` 难度的任务先验证）
   - 示例：
     ```python
     # 实验 N: HyDE + unit + 执行评测（simple only）
     "--rewrite-mode hyde --rag-hyde-route unit --tasks {simple_task_ids}"
     ```

2. **`pipeline.py` — 增强执行失败的信息采集**：
   - 当前 `_execute_generated_code()` 只返回 `(success, output)`
   - 建议增加返回 stderr、exit code、执行时长等信息，写入 JSON 结果

3. **环境检查**：
   - 确认 `conda activate env_genesis` 环境下 Genesis 可正常 headless 运行
   - 确认 `GENESIS_OFFSCREEN=1` + `PYTEST_VERSION=1` 环境变量生效

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `benchmark/run_benchmark_batch.py` | 新增不带 `--no-exec` 的实验组 |
| `benchmark/pipeline.py` | 增强 `_execute_generated_code()` 返回信息 |

**验证**：

```bash
conda activate env_genesis
python -m benchmark.run_benchmark --rewrite-mode hyde --tasks s1_robot_simple_001,s1_rigid_simple_001
```

确认 JSON 中 `execution` 字段有 Pass@1/Pass@3 值，生成的脚本在 `results/tests/` 下可正常运行。

---

### 2.3 激活 Incremental/Dynamic RAG 指标

**现状**：

- `metrics.py` 中 `compute_rag_incremental_metrics(initial, final, expected_apis)` 已完整实现：
  - 计算初始 RAG 命中了哪些 API
  - 计算最终 context 中新增了哪些 API（initial 中没有的）
  - 返回 `new_hit_rate`、`dynamic_slice_hit_rate`、`dynamic_slice_unit_hit_rate`
- 但 `pipeline.py` 中 `_run_task()` 永远将 `rag_hit_after_dynamic` 和 `rag_incremental` 设为 `None`
- `aggregate_metrics()` 中已有这些指标的聚合逻辑，但因为输入全是 None，输出也是 None

**改动方案**：

1. **`pipeline.py` — 在 `_run_task()` 中调用增量指标**：
   - RAG 检索返回后，记录 `initial_context`
   - 如果 agent 做了动态/增量检索（例如基于执行反馈的二次检索），记录 `final_context`
   - 调用 `compute_rag_incremental_metrics(initial_context, final_context, expected_apis)` 计算增量效果
   - 写入结果 JSON

2. **两步实施**：
   - **短期**：即使当前没有动态检索，也可以用 "初始 RAG context" vs "agent 最终使用的 context" 的对比来激活指标（agent 可能在生成时选择了不同的 subset）
   - **中期**：配合改进项 11（retry 注入执行反馈），在 retry 时做增量检索，此时 incremental 指标才有真正意义

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `benchmark/pipeline.py` | `_run_task()` 中调用 `compute_rag_incremental_metrics()` |
| `benchmark/viz_report.py` | 渲染 incremental 指标（确认已有或新增） |

**验证**：

```bash
python -m benchmark.run_benchmark --no-exec --tasks s1_robot_simple_001,s1_sph_fluid_medium_001
```

确认 JSON 中 `rag_hit_after_dynamic` 和 `rag_incremental` 不再是 null。

---

## 三、P1 — 工程质量与一致性

### 3.1 统一 Complexity 命名 ✅ 已完成

**现状**：

- `query.json` 中：
  - `eval_001` ~ `eval_020`：complexity 字段使用 `"hard"`
  - `s1_*` 任务：complexity 字段使用 `"complex"`
  - 两者指同一难度级别
- `metrics.py` 的 `aggregate_metrics()` 按 complexity 分组时，`"hard"` 和 `"complex"` 被当作两个不同的组

**改动方案（二选一）**：

**方案 A — 代码侧兼容（推荐）**：
- 在 `aggregate_metrics()` 中增加映射：`"complex" → "hard"`
- 不修改 `query.json`，兼容历史数据
- 改动位置：`benchmark/metrics.py` 的 `aggregate_metrics()` 函数

**方案 B — 数据侧统一**：
- 在 `query.json` 中将所有 `"complex"` 替换为 `"hard"`
- 风险：影响已有的 benchmark result JSON 中的数据一致性
- 可同时保留代码侧映射以兼容历史结果

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `benchmark/metrics.py` | `aggregate_metrics()` 中增加 `"complex" → "hard"` 映射 |
| `benchmark/query.json` | （可选）统一字段值 |

> **已完成（2026-06-11）**：采用方案 A，在 `benchmark/metrics.py` 的 `aggregate_metrics()` 中增加 `{"complex": "hard"}` 映射。不修改 `query.json`，兼容历史数据。pipeline 透传原始值，metrics 聚合时统一归一化。

---

### 3.2 Batch 配置外部化

**现状**：

- `run_benchmark_batch.py` 中实验组硬编码：
  ```python
  COMMANDS = [
      "--no-exec --rewrite-mode none",
      "--no-exec",                                    # default: hyde + unit
      "--no-exec --rewrite-mode hyde --rag-hyde-route fourway",
  ]
  ```
- 新增或修改实验配置需要改源码

**改动方案**：

1. **支持 YAML 配置文件**：

   ```yaml
   # batch_config.yaml
   name: "default_ablation"
   description: "Rewrite mode + route ablation study"
   base_args: "--no-exec"
   experiments:
     - name: "baseline_none"
       args: "--rewrite-mode none"
     - name: "hyde_unit"
       args: ""  # 使用默认值：hyde + unit
     - name: "hyde_fourway"
       args: "--rewrite-mode hyde --rag-hyde-route fourway"
     - name: "hyde_unit_rerank"
       args: "--rewrite-mode hyde --rerank --rerank-top-n 10"
   ```

2. **`run_benchmark_batch.py` 改动**：
   - 新增 `--config` 参数，接受 YAML 文件路径
   - 加载 YAML 后解析为 COMMANDS 列表
   - 保留默认硬编码配置作为 fallback（不加 `--config` 时行为不变）
   - 每组实验的 `name` 用于命名 `run_01/` 等子目录和 manifest 标签

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `benchmark/run_benchmark_batch.py` | 新增 YAML 加载逻辑 |
| `benchmark/docs/batch_config_example.yaml` | 新增示例配置文件 |

**依赖**：需要 `pyyaml`（通常已安装）

---

### 3.3 解耦 rag_adapter 对 agent 私有方法的依赖

**现状**：

- `rag_adapter.py` 中的 `rag_fast_search()` 直接访问：
  ```python
  agent.rewriter.rewrite(query)
  agent._classify_intent(query)
  agent._retrieve(query, rewrite_mode=..., ...)
  ```
- 这些都是 `GenesisAgent` 的内部实现细节，未来重构 agent 时可能导致 adapter 崩溃

**改动方案**：

1. **`agent.py` — 新增公开方法**：
   ```python
   def retrieve_only(self, query: str) -> dict:
       """
       只执行检索流程（rewrite → classify → retrieve），不生成代码。
       返回与 _retrieve() 相同格式的 dict。
       """
       rewritten = self.rewriter.rewrite(query, mode=self.rewrite_mode)
       intent_tag = self._classify_intent(query)
       return self._retrieve(query, rewrite_mode=self.rewrite_mode,
                             hyde_route=self.hyde_route,
                             tag_filter=intent_tag)
   ```

2. **`rag_adapter.py` — 改用公开方法**：
   ```python
   def rag_fast_search(agent, query):
       retrieval = agent.retrieve_only(query)
       return retrieve_to_knowledge_list(retrieval)
   ```

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `agent.py` | 新增 `retrieve_only()` 公开方法 |
| `benchmark/rag_adapter.py` | `rag_fast_search()` 改用公开方法 |

---

## 四、P2 — 分析与可视化增强

### 4.1 按域（Domain）分组统计

**现状**：

- `query.json` 中 `s1_*` 任务有 `domain` 字段（robot、fluid_mpm、terrain 等），`eval_*` 任务没有
- `aggregate_metrics()` 只按 `overall` + complexity（simple/medium/hard）分组
- HTML 报告只展示 complexity 维度的对比

**改动方案**：

1. **`query.json` — 补全 eval_* 任务的 domain 字段**：
   - 为 20 条 `eval_*` 任务补充 `domain` 字段（根据 query 内容判断）

2. **`metrics.py` — 增加按 domain 聚合**：
   - 在 `aggregate_metrics()` 中新增 domain 分组维度
   - 返回结构增加 `by_domain` 字段：
     ```json
     {
       "by_domain": {
         "robot": {"n": 6, "rag_hit_rate": 0.72, ...},
         "fluid_sph": {"n": 9, "rag_hit_rate": 0.65, ...},
         ...
       }
     }
     ```

3. **`viz_report.py` — 新增 domain 分组图表**：
   - 增加"RAG Hit Rate by Domain"条形图
   - 增加"Per-Domain RAG Hit Rate Heatmap"（多次实验 × 各 domain）

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `benchmark/query.json` | 补全 eval_* 的 domain 字段 |
| `benchmark/metrics.py` | `aggregate_metrics()` 增加 domain 分组 |
| `benchmark/pipeline.py` | 传递 domain 信息 |
| `benchmark/viz_report.py` | 新增 domain 维度图表 |

---

### 4.2 跨 Run 历史趋势图

**现状**：

- `results/runs/` 下有 10+ 次历史运行（2026-06-08 至 2026-06-10）
- `results/batch/` 下有 11 次批量实验
- 没有工具可以追踪指标随时间/参数变化的趋势

**改动方案**：

1. **新建 `visualize_trend.py`**：

   功能：
   - 扫描 `results/runs/` 目录，按时间戳排序加载所有 benchmark JSON
   - 提取每次运行的参数组合和核心指标（RAG hit rate、unit hit rate、Pass@1/3）
   - 按参数组合分组（同一 rewrite_mode + hyde_route 的多次运行归为一组）
   - 生成 Chart.js 折线图：X 轴为时间，Y 轴为指标值
   - 支持按 domain 过滤（只看特定 domain 的趋势）

2. **CLI 接口**：
   ```bash
   python -m benchmark.visualize_trend --runs-dir results/runs/ --output trend.html
   python -m benchmark.visualize_trend --batch-dir results/batch/ --output batch_trend.html
   ```

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `benchmark/visualize_trend.py` | 新建 |

---

### 4.3 Token 效率指标

**现状**：

- 每次 task 的结果 JSON 中记录了 `context_length_initial`（含 tokens 和 chars）
- `aggregate_metrics()` 计算了 `avg_context_tokens_initial`
- 但没有"每千 token 召回了多少 API"的效率指标

**改动方案**：

1. **`metrics.py` — 新增效率指标计算**：
   ```python
   # 在 aggregate_metrics() 中增加
   if avg_tokens > 0:
       group["rag_hit_per_1k_tokens"] = avg_rag_hit_rate / (avg_tokens / 1000)
   else:
       group["rag_hit_per_1k_tokens"] = None
   ```

2. **`viz_report.py` — 展示效率指标**：
   - 在 summary table 中增加 "Hit/1k Tokens" 列
   - 在对比条形图中增加效率指标选项

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `benchmark/metrics.py` | `aggregate_metrics()` 增加 `rag_hit_per_1k_tokens` |
| `benchmark/viz_report.py` | 展示效率指标 |

---

### 4.4 Miss KB Audit 集成到 HTML 报告

**现状**：

- `scripts/analyze_benchmark_miss_kb.py` 生成独立的 markdown 报告
- 输出到与 benchmark JSON 同目录，文件名 `benchmark_miss_kb_audit_*.json/md`
- HTML 可视化中不展示 miss audit 结果

**改动方案**：

1. **`run_benchmark.py` — 在 run 结束后自动触发 miss audit**：
   - 已有 `_run_miss_audit()` 函数，确认它在所有模式下都被调用

2. **`viz_report.py` — 新增 miss audit 章节**：
   - 在单次运行报告中，读取同目录下的 `benchmark_miss_kb_audit_*.json`
   - 渲染两个表格：
     - "Missing from KB"：列出所有 KB 中不存在的 API 及其出现次数
     - "Exists but Not Retrieved"：列出存在但未被检索到的 API 及其出现次数
   - 在多次对比报告中，展示各实验组 miss 分布的差异

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `benchmark/viz_report.py` | 新增 miss audit HTML 章节 |
| `benchmark/run_benchmark.py` | 确认 miss audit 自动触发 |

---

## 五、P3 — 深度改进（可选/后续）

### 5.1 Retry 时注入执行错误反馈

**现状**：

- `pipeline.py` 的 retry 循环（`_run_task()` line 293-336）：
  - 每次调用 `agent.solve(query, knowledge_list=rag_context, save_code=False)`
  - 使用**完全相同的 RAG context**
  - 不将上次执行失败的错误信息传入
  - 相当于"从零重新抽卡"

**改动方案**：

1. **`pipeline.py` — 收集失败信息并注入 retry**：
   ```python
   for attempt in range(max_retries):
       error_feedback = ""
       if attempt > 0 and last_error:
           error_feedback = f"\n[上次执行失败的错误信息]\n{last_error}\n请修复上述错误。"

       result = agent.solve(
           query,
           knowledge_list=rag_context,
           error_feedback=error_feedback,  # 新增参数
           save_code=False
       )
       success, output = _execute_generated_code(code, ...)
       if success:
           break
       last_error = output  # 保留 stderr 用于下次反馈
   ```

2. **`agent.py` — 支持错误反馈参数**：
   - `solve()` 方法新增 `error_feedback: str = ""` 参数
   - 在构建 prompt 时，将 error_feedback 追加到用户消息末尾

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `benchmark/pipeline.py` | `_run_task()` 收集错误并传入 retry |
| `agent.py` | `solve()` 新增 `error_feedback` 参数 |

---

### 5.2 RAG 参数网格搜索

**现状**：

- Batch 只对比 rewrite_mode + hyde_route 的组合
- 未对以下参数做消融实验：
  - `n_api`（默认 6）
  - `n_code`（默认 1）
  - `n_snippet`（默认 3）
  - `n_units`（默认 5）
  - `distance_threshold`（默认 0.5）
  - `use_hybrid`（默认 True）
  - `core_api_limit`（默认 40）

**改动方案**：

1. 基于改进项 3.2（外部化配置），支持参数网格定义：
   ```yaml
   name: "param_grid"
   grid:
     n_api: [3, 6, 10]
     n_units: [3, 5, 8]
     distance_threshold: [0.3, 0.5, 0.7]
   ```
2. 自动展开为所有组合的实验矩阵
3. 每组实验运行后，结果汇总到一个对比报告中

**涉及文件**：`benchmark/run_benchmark_batch.py`

---

### 5.3 Feedback Loop 集成到 Benchmark

**现状**：

- `feedback_loop/` 是完整的离线子系统：
  - Loop A：成功执行 → 知识单元
  - Loop B：失败执行 → 错误记忆
  - Loop C：失败执行 → API 约束
- 与 benchmark 完全独立，benchmark 从未调用 feedback processor

**改动方案**：

1. **`pipeline.py` — 新增 `--feedback` 模式**：
   - 每个 task 执行后，将结果写入 `execution_log.jsonl`
   - 一轮 benchmark 结束后，调用 `feedback_loop/processor.py` 处理日志
   - 更新知识库 JSON 文件
   - 重新灌入 ChromaDB
   - 下一轮 benchmark 使用更新后的 KB

2. **验证效果**：
   - 运行两轮 benchmark：第一轮收集反馈 → 更新 KB → 第二轮对比指标提升

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `benchmark/pipeline.py` | 新增 feedback 模式 |
| `benchmark/run_benchmark.py` | 新增 `--feedback` 参数 |

---

## 六、实施优先级与依赖关系

```
P0.1 接入 Reranker ──────────────┐
P0.2 激活执行评测 ───────────────┤──→ 可并行，无依赖
P0.3 激活 Incremental 指标 ─────┘
         │
         ▼
P1.1 统一 Complexity 命名 ──────┐
P1.2 Batch 配置外部化 ───────────┤──→ 可并行，无依赖
P1.3 解耦 rag_adapter ──────────┘
         │
         ▼
P2.1 Domain 分组统计 ─── 依赖 P1.1
P2.2 历史趋势图 ──────── 独立
P2.3 Token 效率指标 ──── 独立
P2.4 Miss Audit 集成 ─── 独立
         │
         ▼
P3.1 Retry 错误反馈 ───── 依赖 P0.2
P3.2 参数网格搜索 ─────── 依赖 P1.2
P3.3 Feedback Loop ────── 依赖 P0.2 + P3.1
```

---

## 七、各改进项的预估工作量

| 编号 | 改进项 | 涉及文件数 | 预估代码量 |
|------|--------|-----------|-----------|
| P0.1 | 接入 Reranker | 2-3 | ~80 行 |
| P0.2 | 激活执行评测 | 2 | ~40 行（主要是验证环境） |
| P0.3 | 激活 Incremental 指标 | 2 | ~30 行 |
| P1.1 | 统一 Complexity 命名 | 1-2 | ~10 行 |
| P1.2 | Batch 配置外部化 | 1-2 | ~60 行 |
| P1.3 | 解耦 rag_adapter | 2 | ~20 行 |
| P2.1 | Domain 分组统计 | 4 | ~120 行 |
| P2.2 | 历史趋势图 | 1（新建） | ~200 行 |
| P2.3 | Token 效率指标 | 2 | ~20 行 |
| P2.4 | Miss Audit 集成 | 1-2 | ~80 行 |
| P3.1 | Retry 错误反馈 | 2 | ~50 行 |
| P3.2 | 参数网格搜索 | 1 | ~100 行 |
| P3.3 | Feedback Loop 集成 | 2 | ~100 行 |

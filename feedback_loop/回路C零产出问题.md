# 问题：feedback_loop 回路 C 在 100 条 prompt 上颗粒无收

> 写给专家 AI。请先通读再动手。

## 解决状态（2026-07-12）

该问题已经解决。根因不是回路 C 的正则整体失效，而是处理器把截断后的 `stdout/stderr` 传给回路 C，没有使用日志中保存的完整 traceback artifact 或 `concise_error`。处理器现已优先读取完整 traceback，并以 `concise_error` 作为兼容回退。

使用 `--loops c --reprocess` 对原 100 条日志离线重放后，结果如下：

| 日志 | 失败记录 | C 候选 |
|---|---:|---:|
| part1 | 12 | 0 |
| part2 | 15 | 1 |
| part3 | 26 | 3 |
| part4 | 8 | 1 |

共得到 5 条候选记录，覆盖 4 个唯一 API、6 条约束。候选已按测试批次归档于 `feedback_loop/data/loop_c/runs/`，累计视图为 `feedback_loop/data/loop_c_summary.json`；尚未人工批准，也未写入正式服务知识库。本文其余内容保留为原始故障诊断记录。

## 背景（30 秒版）

我们有一个物理仿真 RAG 系统（`rag_demo/`），运行在 `D:\Desktop\Genesis\Genesis-main\rag_demo\`。它的 `feedback_loop/` 子系统负责：

- 跑 benchmark prompt → Agent 生成代码 → 执行代码 → **从失败中提炼知识，回流到知识库**

三条反馈回路中，**回路 C** 的职责是：从执行失败的 stderr/traceback 中**自动提取 API 使用约束**（如"`add_camera` 必须在 `build()` 前调用"、"`gs.morphs.Box` 不接受 `center` 参数，应该用 `pos`"）。

## 现状

刚跑完 `benchmark/query.json` 的 100 条 prompt：

| 指标 | 数值 |
|---|---|
| 总执行 | 100 |
| 成功 | 39 |
| 失败 | 61 |
| 回路 B 候选（错误记忆） | 56 |
| **回路 C 候选（API 约束）** | **0** |

**61 条失败中，回路 C 没有产出任何一条 API 约束。** 这不应该——61 条里肯定有 API 误用导致的失败。

## 回路 C 的当前实现

代码路径：`feedback_loop/loop_c/constraint_builder.py`

流程：
```
stderr → parse_error_events() → map_events_to_api() → _heuristic_constraints()
```

### parse_error_events() (line 376)

用正则从日志文本中匹配错误行。匹配两种模式：
- `[Genesis]... [ERROR]... XxxError: message` → confidence=high
- `XxxError: message`（标准 Python traceback 行）→ confidence=medium

### map_events_to_api() (line 559)

从错误消息中提取 API 符号（如 `gs.morphs.Box(...)`），映射到 `genesis_api_index.json` 中的标准 API ID（654 个已知 API）。

符号提取逻辑 `_symbol_from_error_message()` (line 458) 匹配：
- `Xxx() got an unexpected keyword argument 'yyy'`
- `Xxx() missing required argument`
- `Xxx() got multiple values for argument 'yyy'`
- `Xxx() takes N positional arguments but M were given`
- `'Xxx' object has no attribute 'yyy'`
- `name 'Xxx' is not defined`
- `No module named 'Xxx'`

fallback `_symbol_from_traceback()` (line 482)：从 traceback 帧中提取 `gs.xxx.yyy(` 调用。

### _heuristic_constraints() (line 223)

对每条 mapped event，按错误文本模式生成一句话约束，例如 `"Do not pass unsupported keyword 'center' to gs.morphs.Box; follow the exact signature."`。之前有一个 catch-all fallback `f"Avoid this runtime failure pattern: {msg}"` 会把无法泛化的错误原文贴进去——**已在上轮优化中删除**（`constraint_builder.py line 299`，`continue` 跳过）。所以现在遇到不匹配任何已知模式的错误时，什么也不产出。

## 最可能的原因

61 条失败的 stderr 没有命中上述任何一条正则。可能是：

1. **Genesis 的错误格式不走标准 Python**。`GenesisException`、Taichi kernel 编译错误、CUDA 错误等不是 `XxxError: message` 格式
2. **traceback 中提取不到 `gs.xxx()` 调用**。`_symbol_from_traceback` 的 skip 逻辑可能过于激进（跳过了 `genesis\` 内部帧）
3. **错误被 parse 到了但 map 不到已知 API ID**。正则能从错误文本里抓到符号，但 `resolve_api_id()` 映射到 654 个标准 API ID 时失败

## 建议的排查路径

1. **抽样检查**：从 4 个 execution_log 各取 2 条失败记录，手工看 `concise_error` 长什么样，和现有正则比照
2. **在 `_heuristic_constraints` 中加调试输出**：跑一条失败记录，看 `parse_error_events` 抓到了几条、`map_events_to_api` 映射成功了几条
3. **针对性扩展**：根据实际错误文本格式，增补正则规则
4. **考虑轻量 LLM 路径**：如果纯正则确实覆盖不全，可以在 `_heuristic_constraints` 前面加一层 LLM 约束生成（仅对映射成功但启发式没命中 API 的事件），成本远低于之前全量 LLM Judge

## 关键文件

| 文件 | 行数 | 角色 |
|---|---|---|
| `feedback_loop/loop_c/constraint_builder.py` | ~850 | 回路 C 完整实现 |
| `feedback_loop/processor.py` | ~750 | 调用回路 C，生成 pending_review |
| `workspace/logs/execution_log_query100_part1~4.jsonl` | 100 行 | 执行日志，每条含 `concise_error` |
| `feedback_loop/data/loop_b/runs/` | 4 个批次 | 已迁移的 B 候选结构化数据 |
| `knowledge_base/genesis_api_index.json` | 654 API | API ID 映射目标 |
| `feedback_loop/data/loop_c/approved/api_constraint.json` | 9 API | 当前约束 staging 基线（手工产物，非本轮产出） |
| `feedback_loop/GOAL_20260708_feedback_loop_run.md` | — | 本轮任务 GOAL |

Python 路径：`D:\anaconda\envs\env_genesis\python.exe`，所有命令前加 `PYTHONIOENCODING=utf-8`。

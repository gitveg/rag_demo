# debug/ — 调试与验证实验专用目录

这个目录专门存放**小规模、临时性**的 benchmark 跑批，用于：

- 改完 RAG/pipeline 代码后，跑 1~4 个任务确认检索没崩（冒烟测试）
- 验证某个新参数 / 新路由 / 重构是否生效
- 快速复现某个任务的检索细节（配合 `--tasks` 自动开详细报告）

## 用法

跑这类实验时，统一用 `--output-dir` 指到这里，并给个有意义的子名：

```bash
# 冒烟测试（改完代码后）
python benchmark/run_benchmark.py --no-exec --tasks eval_001 \
  --output-dir benchmark/results/debug/smoke_after_refactor

# 验证 rerank 参数
python benchmark/run_benchmark.py --no-exec --tasks eval_001,eval_002 \
  --output-dir benchmark/results/debug/verify_rerank_topn

# 复现某个任务的检索细节
python benchmark/run_benchmark.py --no-exec --tasks eval_006 \
  --output-dir benchmark/results/debug/repro_eval006
```

## 命名约定

`debug/<目的>_<上下文>`，例如：
- `smoke_<改动描述>` — 冒烟测试
- `verify_<验证对象>` — 参数/路由验证
- `repro_<task_id>` — 单任务复现

## 与其他目录的区别

| 目录 | 用途 | 规模 |
|---|---|---|
| **`debug/`** ← 本目录 | 临时调试/验证（可随时清） | 1~4 任务，通常 `--no-exec` |
| `runs/` | 单次正式 run（默认输出） | 全量 |
| `batch/` | 批量对比实验 | 多组配置 |
| `tests/` | `_execute_generated_code()` 写的临时 `.py` | 自动产生 |

## 清理

这个目录下的内容**都是临时的**，可以定期整体清空，不影响任何正式结果。

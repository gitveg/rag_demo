# 执行反馈循环

> 当前状态：Phase 0 已于 2026-07-11 实施。默认只运行 Loop B/C；Loop A 保持关闭。

本模块把代码生成和执行结果转换为可审核的知识候选。当前原则是：执行事实完整记录、环境失败不进入知识、所有入库默认 fail-closed。

完整的 v2 架构与后续迁移见 [`docs/feedback_loop_v2_design.md`](../docs/feedback_loop_v2_design.md)。

面向 Loop B/C 的生产化质量标准、精准触发、简洁性约束与分阶段落地计划见
[`docs/feedback_loop_bc_production_plan.md`](../docs/feedback_loop_bc_production_plan.md)。

## 当前数据流

```text
prompt
  -> GenesisAgent 生成代码
  -> 不可变代码与输出 artifacts
  -> execution event JSONL
  -> 失败分类
  -> Loop B/C 候选
  -> pending review
  -> 显式批准
  -> knowledge_base JSON
```

`returncode == 0` 只表示 `process_passed`，不表示物理正确。当前执行器不会产生 `verified_passed`，因此 Loop A 即使被显式选择也不会产生知识单元候选。

## 安全边界

- 生成失败、空代码也必须写终态 event。
- Timeout 保留已经产生的 stdout/stderr。
- dependency、resource、timeout、infrastructure、engine internal 和 syntax 失败不进入 B/C。
- C 使用完整 traceback artifact 或 `concise_error`，不再依赖截断后的 stderr。
- 所有候选默认 pending；`--approve` 必须显式提供 `--ids`。
- 正式 KB JSON 使用临时文件原子替换，并保留上一版 `.bak`。
- Loop A 需要 `verified_passed`，默认处理模式为 `bc`。
- 进度以稳定 event ID 去重；旧日志仍兼容 basename/offset 迁移。

## 运行

### 1. 生成、执行、收集

```powershell
python feedback_loop/run_and_collect.py `
  --prompts benchmark/query.json `
  --log workspace/logs/execution_log.jsonl
```

常用参数：

- `--start-index N`
- `--max-prompts N`
- `--timeout SECONDS`
- `--run-id ID`
- `--rewrite-mode none|translate|hyde`
- `--auto-process`：执行后自动以 `--loops bc` 处理

每次运行的不可变产物位于：

```text
workspace/runs/<run_id>/<prompt_index>_<task_id>/attempt_1/
  code.py
  stdout.txt
  stderr.txt
  traceback.txt
```

### 2. 生成待审候选

```powershell
python feedback_loop/processor.py `
  --log workspace/logs/execution_log.jsonl `
  --loops bc
```

输出：

```text
feedback_loop/data/loop_a/runs/<test>/<YYYYMMDD-HHMMSS-micros>/review.md
feedback_loop/data/loop_a/runs/<test>/<YYYYMMDD-HHMMSS-micros>/candidates.json
feedback_loop/data/loop_b/runs/<test>/<YYYYMMDD-HHMMSS-micros>/review.md
feedback_loop/data/loop_b/runs/<test>/<YYYYMMDD-HHMMSS-micros>/candidates.json
feedback_loop/data/loop_c/runs/<test>/<YYYYMMDD-HHMMSS-micros>/review.md
feedback_loop/data/loop_c/runs/<test>/<YYYYMMDD-HHMMSS-micros>/candidates.json
```

每个 `<test>/<YYYYMMDD-HHMMSS-micros>` 是一次可独立审核的测试批次，例如 `online-full/20260712-183541-850553` 或 `q100-p3/20260710-214221`。`feedback_loop/data/loop_a_summary.json`、`loop_b_summary.json`、`loop_c_summary.json` 分别是从各自所有运行归档自动重建的跨测试累计候选，不代表已批准或已发布的知识。

需要对旧日志重新生成候选时，使用 `--reprocess`。该模式忽略已有 progress，但不修改 progress，也不会自动批准或写入约束文件：

```powershell
python feedback_loop/processor.py `
  --log workspace/logs/execution_log.jsonl `
  --loops c `
  --reprocess
```

Loop B 当前收集原始代码和错误证据。批准前必须在候选 JSON 的 `raw` 中填写：

- `bad_pattern`
- `correction`
- `explanation`
- `tags`

### 3. 显式批准

```powershell
python feedback_loop/processor.py `
  --approve feedback_loop/data/loop_c/runs/<log>/<timestamp>/candidates.json `
  --ids "B:1,C:0"
```

默认 `--ids` 为空，不会批准任何候选。批准时会校验：

- A：完整知识单元字段；
- B：错误模式、修正、解释和 tags；
- C：API ID 存在，约束非空，entry 与候选一致。

### 4. 当前兼容发布流程

Loop C 批准后先写入 `feedback_loop/data/loop_c/approved/api_constraint.json`。若仍使用现有 Chroma API 文档，需要显式合并和重新构建：

```powershell
python feedback_loop/processor.py --merge-constraints-to-api-index
python rag_engine.py
```

此流程是 Phase 0 兼容路径。v2 目标是 reviewed constraint overlay，不再修改静态 API index，也不因约束文本更新重建 API embedding。

## Event v2

新记录包含：

- `schema_version/run_id/event_id`
- `prompt_index/prompt_hash`
- `code_sha256`
- `stage/outcome/failure_category`
- `verified_success`
- `environment`
- `artifacts`
- `knowledge_ids/retrieval_trace`

旧版 execution log 仍可处理，其 event ID 会按记录内容确定性生成。

## 失败分类

```text
generation_failed
static_invalid
infra_failed
dependency_failed
resource_failed
timed_out
runtime_failed
process_passed
verified_passed
```

Phase 0 分类器是确定性规则，目的是先隔离明确的非知识失败。Phase 1 会进一步建立 traceback user frame、AST 调用定位和统一 diagnosis。

## 测试

```powershell
python -m unittest discover -s feedback_loop/tests -v
```

测试不调用模型、网络或 Genesis，覆盖事件 ID、生成失败落盘、Timeout 部分输出、环境失败隔离、C 完整错误解析、A 序列化、审批校验、事件幂等和原子备份。

## 文件

```text
feedback_loop/
  data/
    loop_a/                A 回路的单次运行与拒绝记录
      runs/<log>/<timestamp>/{review.md,candidates.json}
      rejected/
    loop_b/                B 回路的单次运行与拒绝记录
      runs/<log>/<timestamp>/{review.md,candidates.json}
      rejected/
    loop_c/                C 回路的单次运行、拒绝记录和已批准约束
      runs/<log>/<timestamp>/{review.md,candidates.json}
      rejected/
      approved/api_constraint.json
    loop_a_summary.json    A 的跨测试累计候选
    loop_b_summary.json    B 的跨测试累计候选
    loop_c_summary.json    C 的跨测试累计候选
    state/execution_feedback_progress.json
  event_schema.py          Event v2 ID、环境指纹与校验
  failure_classifier.py    Phase 0 失败分类
  run_and_collect.py       生成、执行、artifact 和 event 收集
  processor.py             B/C 候选、审核和兼容发布
  gates.py                 待审 Markdown 格式
  utils.py                 JSON/JSONL、API 与约束工具
  loop_b/judge.py          B 原始证据收集
  loop_c/constraint_builder.py
  tests/
```

`问题回应.md` 与 `问题诊断与回应汇总.md` 是历史决策记录，不再表示当前运行状态。

# Goal: 跑 query.json 产出回路 B/C 结果

> 日期：2026-07-08
> 范围：`rag_demo/feedback_loop/`
> 目标读者：新开的 Codex 对话
> 当前策略：跑内部 `benchmark/query.json` 的 100 个 prompt，但本轮只关心回路 B/C 内容产出，不做 pass rate 评测，不启用回路 A。

---

## 1. 本轮目标

跑完 `rag_demo/benchmark/query.json` 中的 100 条 prompt，得到一版来自真实执行失败的回路 B/C 结果：

```text
B: 错误记忆候选 / 入库内容
C: API 约束候选 / 入库内容
```

本轮重点不是“成功率提高了多少”，而是：

- 失败样本是否能产出高质量错误记忆
- 错误记忆是否能写成清楚的 `bad_pattern / correction / explanation / tags`
- API 约束是否准确、稳定、可泛化
- 是否避免 CUDA / driver / OOM / Taichi backend 等环境噪声污染约束

本轮暂不做：

- 不启用回路 A
- 不把成功代码写成知识单元
- 不做 pass rate 对比报告
- 不自动 merge 到 `genesis_api_index.json`
- 不自动重新灌库

---

## 2. 关键背景

项目根目录：

```text
D:\Desktop\Genesis\Genesis-main\rag_demo
```

Python：

```text
D:\anaconda\envs\env_genesis\python.exe
```

Prompt 文件：

```text
benchmark\query.json
```

当前 `benchmark/query.json` 有 100 条内部任务，每条包含：

- `task_id`
- `complexity`
- `query`
- `expected_apis`
- `evaluation_rules`

已知重要修复：

- `run_and_collect.py` 已写入顶层 `concise_error`
- `processor.py` 已优先读取顶层 `concise_error`
- `run_and_collect.py` 已新增 `--start-index`，可以分批跑

当前已有内容：

- `knowledge_base/genesis_error_memory.json` 已有 9 条手建错误记忆，可作为 B baseline
- `knowledge_base/api_constraint.json` 当前已有一版 Codex 从 baseline B 提炼的 C v0，9 个 API / 9 条约束
- 新跑 query 后产生的候选应单独审查；不要把旧 baseline 和新 query 结果混在一起误判

---

## 3. 总体流程

```text
Step 0  代码健康检查
Step 1  分批跑 100 条 prompt，生成 execution_log_*.jsonl
Step 2  对每个 log 跑 processor.py --loops bc
Step 3  Codex 审查 pending_review / pending_candidates
Step 4  Codex 补齐 B 候选字段，筛选 B/C approve IDs
Step 5  approve 入库到 error_memory / api_constraint
Step 6  输出 B/C 结果总结
```

不要使用 `run_and_collect.py --auto-process`。

原因：

- 本轮只跑 B/C，必须显式执行 `processor.py --loops bc`
- `--auto-process` 不利于分批审查和定位问题

---

## 4. Step 0: 代码健康检查

```powershell
cd D:\Desktop\Genesis\Genesis-main\rag_demo
$env:PYTHONIOENCODING = "utf-8"
& D:\anaconda\envs\env_genesis\python.exe -m py_compile `
  feedback_loop\run_and_collect.py `
  feedback_loop\processor.py `
  feedback_loop\gates.py `
  feedback_loop\loop_b\judge.py `
  feedback_loop\loop_c\constraint_builder.py
```

如果这里失败，先修代码，不要继续跑 100 条。

---

## 5. Step 1: 分批跑 100 条 prompt

建议分 4 批跑，避免一次运行太久后不好恢复：

```powershell
cd D:\Desktop\Genesis\Genesis-main\rag_demo
$env:PYTHONIOENCODING = "utf-8"

& D:\anaconda\envs\env_genesis\python.exe feedback_loop\run_and_collect.py `
  --prompts benchmark\query.json `
  --start-index 0 `
  --max-prompts 30 `
  --timeout 120 `
  --log workspace\logs\execution_log_query100_part1.jsonl

& D:\anaconda\envs\env_genesis\python.exe feedback_loop\run_and_collect.py `
  --prompts benchmark\query.json `
  --start-index 30 `
  --max-prompts 30 `
  --timeout 120 `
  --log workspace\logs\execution_log_query100_part2.jsonl

& D:\anaconda\envs\env_genesis\python.exe feedback_loop\run_and_collect.py `
  --prompts benchmark\query.json `
  --start-index 60 `
  --max-prompts 30 `
  --timeout 120 `
  --log workspace\logs\execution_log_query100_part3.jsonl

& D:\anaconda\envs\env_genesis\python.exe feedback_loop\run_and_collect.py `
  --prompts benchmark\query.json `
  --start-index 90 `
  --max-prompts 10 `
  --timeout 120 `
  --log workspace\logs\execution_log_query100_part4.jsonl
```

每批结束后记录：

- 总条数
- 成功数
- 失败数
- 是否出现生成失败
- log 路径

---

## 6. Step 2: 处理日志，只跑 B/C

每个 log 跑一次：

```powershell
$env:PYTHONIOENCODING = "utf-8"

& D:\anaconda\envs\env_genesis\python.exe feedback_loop\processor.py `
  --log workspace\logs\execution_log_query100_part1.jsonl `
  --loops bc

& D:\anaconda\envs\env_genesis\python.exe feedback_loop\processor.py `
  --log workspace\logs\execution_log_query100_part2.jsonl `
  --loops bc

& D:\anaconda\envs\env_genesis\python.exe feedback_loop\processor.py `
  --log workspace\logs\execution_log_query100_part3.jsonl `
  --loops bc

& D:\anaconda\envs\env_genesis\python.exe feedback_loop\processor.py `
  --log workspace\logs\execution_log_query100_part4.jsonl `
  --loops bc
```

预期输出：

```text
workspace\pending_reviews\pending_review_*.md
workspace\pending_reviews\pending_candidates_*.json
```

如果某一批没有候选，记录原因：

- 全部成功
- 失败全是超时 / 环境问题 / 无错误摘要
- 启发式过滤掉
- 与现有错误记忆重复

---

## 7. Step 3: Codex 审查 B/C 候选

用户不逐条审核，Codex 代审。

对每个 `pending_candidates_*.json`：

### B 候选审查

Approve 条件：

- 错误和 Genesis API 使用方式明确相关
- 错误模式未来可能复现
- 能写出明确的：
  - `bad_pattern`
  - `correction`
  - `explanation`
  - `tags`

Reject 条件：

- 只是 CUDA / driver / OOM / Taichi backend 环境问题
- 只是超时，没有明确 API 错误
- traceback 不完整，不能可靠归因
- 只是通用 Python 语法或变量名问题，和 Genesis API 关系弱
- 与现有 `genesis_error_memory.json` 重复

重要：

`processor.py --approve` 会跳过没有 `bad_pattern` 的 B 候选。
因此 Codex 必须在 approve 前编辑 `pending_candidates_*.json`，把通过审核的 B 候选里的 `raw.bad_pattern / raw.correction / raw.explanation / raw.tags` 补齐。

### C 候选审查

Approve 条件：

- `api_id` 存在于 `knowledge_base/genesis_api_index.json`
- 约束是稳定 API 使用规则
- 约束短、清楚、可操作
- 约束能帮助未来生成器避免同类错误

Reject 条件：

- 把环境错误归因成 API 约束
- 只是复述错误日志，没有约束价值
- 约束过宽，可能限制合法用法
- `api_id` 映射不稳或不存在

---

## 8. Step 4: approve 入库

先汇总每个 pending 文件的审查结果：

```text
pending_candidates_xxx.json
  approve: B:0,B:3,C:1
  reject: B:1 because ...
  reject: C:0 because ...
```

然后执行：

```powershell
$env:PYTHONIOENCODING = "utf-8"
& D:\anaconda\envs\env_genesis\python.exe feedback_loop\processor.py `
  --approve workspace\pending_reviews\pending_candidates_TIMESTAMP.json `
  --ids "B:0,B:3,C:1"
```

注意：

- 不要盲目用 `--ids all`
- 不要盲目用 `C:all`
- 每批 approve 前都要先说明批准和拒绝理由

---

## 9. Step 5: 本轮先不要 merge / 灌库

本轮目标是得到 B/C 结果，先停在：

```text
knowledge_base/genesis_error_memory.json
knowledge_base/api_constraint.json
```

暂不执行：

```powershell
feedback_loop\processor.py --merge-constraints-to-api-index
python rag_engine.py
```

等用户看过 B/C 结果后，再决定是否 merge 和重新灌库。

---

## 10. 最终交付物

新对话完成后，需要汇报：

```text
执行日志:
  - part1: 成功 x / 失败 y / 候选 B a / C b
  - part2: ...
  - part3: ...
  - part4: ...

回路 B:
  - 新增错误记忆数量
  - 每条 bad_pattern / correction 摘要
  - 拒绝数量和主要原因

回路 C:
  - 新增/更新 API 约束数量
  - 每个 api_id 的约束摘要
  - 拒绝数量和主要原因

文件:
  - knowledge_base/genesis_error_memory.json
  - knowledge_base/api_constraint.json
  - workspace/pending_reviews/pending_review_*.md
  - workspace/pending_reviews/pending_candidates_*.json

风险:
  - 哪些候选不确定
  - 哪些错误可能是环境问题
  - 是否建议进入 merge / 灌库
```

---

## 11. 当前基线说明

在开始 query100 之前，当前知识库已有：

- B baseline：`genesis_error_memory.json` 中 9 条手建错误记忆
- C baseline：`api_constraint.json` 中 9 个 Codex 保守约束

query100 产生的是新执行日志驱动的增量结果。

如果用户要求“只看 query100 产生的纯新增结果”，以 `pending_candidates_*.json` 和本轮 approve 摘要为准。
如果用户要求“看最终知识库状态”，以 `genesis_error_memory.json` 和 `api_constraint.json` 为准。

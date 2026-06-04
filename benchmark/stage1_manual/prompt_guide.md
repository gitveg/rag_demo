# Prompt 构建指导文档

> 用于指导 Genesis RAG Agent 的测试 Prompt 构建，服务于 `build_api_constraint` 约束自动提取管线。

---

## 1. 目标

为 `build_api_constraint.py` 提供多样化的 Prompt，让 Agent 生成代码 → 执行 → 捕获运行时错误 → 自动提取 API 约束（anti-hallucination rules）。

Prompt 越能触发 Agent 的 API 幻觉，产出的约束越有价值。

---

## 2. 难度分级定义

### 简单
- **范围**：只包含**一个子任务**
- **实体**：仅涉及一个基本几何体（Sphere / Box / Cylinder / Plane）
- **材质**：仅限刚体（`gs.materials.Rigid`）
- **状态**：简单的静止或自由落体
- **颜色**：可有可无
- **示例**：`A rigid sphere falls onto the ground.`

### 中等
- **范围**：包含 **2-5 个子任务**的糅合
- **实体**：基本几何体，数量 1-3 个
- **材质**：不局限于刚体
- **状态**：可以是简单的，也可以稍微复杂一点
- **颜色**：可有可无
- **要点**：相比简单，各属性挑 2-3 个进行复杂化，并非每个属性都要变复杂
- **示例**：`Create two rigid spheres side by side, falling onto the ground at the same time.`

### 复杂
- **范围**：长程复杂任务，可能涉及多个阶段
- **实体**：可能涉及非基本几何体（资产导入：Mesh / MJCF / URDF）
- **材质**：任意材质，可能涉及材质交叉（刚体 + 软体 / 刚体 + 流体等）
- **状态**：相对复杂（多步交互、运动控制等）
- **示例**：`Load a Franka robot arm from an XML file and place a red rigid box on the ground in front of it.`

---

## 3. 领域清单

以下定义了所有需要覆盖的领域，含统一的 `domain_tag`。所有产出（手写、外部专家、LLM 增广）必须使用相同的 tag，确保 `task_id` 命名一致。

| domain_tag | 领域名称 | 当前覆盖 | 说明 |
|---|---|---|---|
| `rigid` | 刚体 | 已覆盖（6 个） | 基础刚体仿真，当前已充分覆盖 |
| `mpm_elastic` | MPM 弹性体 | 已覆盖（2 个） | 使用 MPM.Elastic 材质的软体 |
| `mpm_fluid` | MPM 流体 | 已覆盖（2 个） | 使用 MPM.Liquid 材质的流体 |
| `fem_elastic` | FEM 弹性体 | **未覆盖** | 使用 FEM.Elastic 材质，易与 MPM.Elastic 混淆 |
| `fem_cloth` | 布料 | **未覆盖** | 使用 FEM.Cloth 材质模拟织物 |
| `sph_fluid` | SPH 流体 | **未覆盖** | 使用 SPH.Liquid 材质，易与 MPM.Liquid 混淆 |
| `mpm_sand` | MPM 沙粒 | **未覆盖** | 使用 MPM.Sand / MPM.Snow 材质 |
| `surface` | 表面着色 | **未覆盖** | 颜色、纹理、材质外观设置 |
| `camera` | 相机与录制 | **未覆盖** | 相机创建、视角控制、视频录制 |
| `force_field` | 力场 | **未覆盖** | 持续外力（风力、磁场等） |
| `terrain` | 地形 | **未覆盖** | 使用 Terrain morph 生成地形 |
| `drone` | 无人机 | **未覆盖** | 使用 Drone morph |
| `sensor` | 传感器 | **未覆盖** | Lidar / IMU / 深度相机等 |
| `robot` | 机器人控制 | 仅加载（1 个） | 加载后的关节控制、运动规划 |
| `cross_domain` | 跨域交互 | 少量 | 多种材质/物理类型交叉耦合 |

**优先级**：未覆盖的 11 个域为第一阶段重点，`cross_domain` 额外补充 2-3 个。`rigid` / `mpm_elastic` / `mpm_fluid` 已有覆盖，第一阶段可不额外手写。

---

## 4. Prompt 格式规范

每个 Prompt 为一个 JSON 对象，字段如下：

```json
{
  "task_id": "domain_simple_001",
  "complexity": "simple",
  "domain": "fem",
  "query": "英文自然语言描述，清晰无歧义"
}
```

**字段说明**：
- `task_id`：`s1_{domain_tag}_{complexity}_{序号}` 格式（Stage 2 改前缀为 `s2_`）
- `complexity`：`simple` / `medium` / `complex`
- `domain`：取第 3 节清单中的 `domain_tag`
- `query`：纯英文描述，不要出现中文
- **不包含** `expected_apis`（后续有专门的 pipeline 自动补充）

**示例**：`s1_fem_cloth_medium_002` 表示 Stage 1、布料域、中等难度、第 2 个

---

## 5. Prompt 质量标准

好的 Prompt 应该满足：

1. **明确性**：任务描述清晰，不存在歧义。Agent 看到后能确定要做什么。
2. **API 触发性**：能触发特定域的 API 调用（比如要求 "soft elastic" 就必须用 FEM/MPM material）。
3. **幻觉诱导性**：自然地让 Agent 可能犯错（比如 "static box" 容易诱导把 `static=True` 传给 morph 而非 entity）。
4. **不指定实现细节**：不要在 query 里写 "用 gs.morphs.Sphere" 这种提示，要考验 Agent 自己选 API 的能力。
5. **可执行性**：描述的场景在物理上是合理的，Agent 生成的代码理论上可以跑通。

---

## 6. 跨域交叉 Prompt

除了单域 Prompt，额外需要 2-3 个跨域 Prompt，因为跨域场景更容易触发 solver 配置和材质路径的幻觉：

- 刚体 + 软体交互（如刚体球砸在弹性板上）
- 刚体 + 流体交互（如球落入水池）
- 机器人 + 软体交互（如机械臂抓取弹性物体）
- 布料 + 刚体交互（如布料覆盖在盒子上）

---

## 7. 文件结构

```
rag_demo/benchmark/
├── query.json                          # 原始 20 个 prompt（保留不动）
├── stage1_manual/                      # 第一阶段：手写精选
│   ├── prompt_guide.md                 # 本文档
│   ├── rag_demo_prompts.json           # Claude 生成的 prompt
│   └── external_prompts/               # 外部 AI 专家生成的 prompt
│       ├── gemini_prompts.json
│       └── chatgpt_prompts.json
├── stage2_augmented/                   # 第二阶段：LLM 自动增广
│   └── augmented_prompts.json
└── merged/                             # 最终合并
    └── full_query.json
```

---

## 8. 给外部 AI 专家的 Prompt 模板

> 将以下内容发给 Gemini / ChatGPT，请它们按要求生成 Prompt。

---

### 附：外部专家 Prompt 模板

```
你是一位物理仿真领域的专家。我们正在为一个 LLM 代码生成 Agent 构建测试用例。

该 Agent 的任务是根据用户的自然语言描述，自动生成 Genesis 物理引擎的 Python 仿真代码。
Genesis 是一个类似 MuJoCo / PyBullet 的机器人与物理仿真平台，支持：
刚体、软体（弹性体/布料）、流体（MPM/SPH）、机器人（URDF/MJCF）、力场、传感器、相机录制、地形、无人机等。

我们需要你生成自然语言 Prompt 来测试这个 Agent。**请不要在 Prompt 中指定任何 API 名称或实现细节**，
模拟一个不懂 API 的真实用户会怎么描述仿真需求。

## 需要覆盖的领域

请为以下每个 domain 各生成 3 个 Prompt（简单/中等/复杂各一个）：

| domain（用于 JSON 字段） | 领域 | 说明 |
|---|---|---|
| `fem_elastic` | FEM 弹性体 | 柔软有弹性的固体变形和弹跳 |
| `fem_cloth` | 布料 | 布料/织物的飘动、下垂、覆盖 |
| `sph_fluid` | SPH 流体 | 水和液体的流动飞溅（粒子风格） |
| `mpm_sand` | MPM 沙粒 | 沙粒的堆积和坍塌 |
| `surface` | 表面着色 | 给物体设置颜色、金属质感等外观 |
| `camera` | 相机与录制 | 从特定视角观看并录制仿真过程 |
| `force_field` | 力场 | 给物体施加持续外力（风力、向上推力等） |
| `terrain` | 地形 | 起伏不平的地形场景 |
| `drone` | 无人机 | 无人机飞行控制 |
| `sensor` | 传感器 | Lidar / IMU / 深度相机等感知设备 |
| `robot` | 机器人控制 | 让机器人手臂运动到指定姿态或执行动作 |
| `cross_domain` | 跨域交互 | 2-3 个即可，如刚体落入水中、机器人抓软体等 |

## 难度定义

- **简单**：只包含一个子任务。实体仅限一个基本几何体，材质仅限一种，状态简单（静止或自由落体）。颜色可有可无。
  示例：`A rigid sphere falls onto the ground.`
- **中等**：包含 2-5 个子任务的糅合。实体可以是 1-3 个基本几何体，材质可以不限于刚体但尽量以刚体为主，状态可以稍复杂。各属性挑 2-3 个进行复杂化即可。
  示例：`Create two rigid spheres side by side, falling onto the ground at the same time.`
- **复杂**：长程复杂任务，可能涉及非基本几何体（资产导入如 Mesh/MJCF/URDF），材质交叉，状态复杂。
  示例：`Load a Franka robot arm and place a red rigid box on the ground in front of it.`

## Prompt 质量要求

1. 用英文描述，清晰无歧义
2. 不要在 Prompt 里指定具体 API 名称或实现细节
3. 场景在物理上合理

## 输出格式

请输出一个 **格式化** 的 JSON 数组（使用缩进，每个对象独占多行）。

每个元素格式如下：
{
  "task_id": "s1_{domain}_{complexity}_{三位序号}",
  "complexity": "simple 或 medium 或 complex",
  "domain": "上表中的 domain 值",
  "query": "英文 Prompt 描述"
}

其中 task_id 的 domain 必须严格使用上表第一列的值。

请直接输出 JSON 数组，不要包裹在 markdown 代码块中。确保每个 JSON 对象的每个字段各占一行。
```

---

## 9. 时间线

1. **当前**：产出指导文档 + Claude 手写 prompt + 外部专家 prompt 模板
2. **下一步**：收集三方 prompt → 合并去重 → 形成 stage1 成果
3. **之后**：基于 stage1 成果，构建 stage2 自动增广 pipeline
4. **最终**：合并为 `full_query.json`，跑 `build_api_constraint` 全量约束提取

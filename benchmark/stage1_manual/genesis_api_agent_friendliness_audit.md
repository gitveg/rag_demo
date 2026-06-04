# Genesis API 缺陷审查报告：Agent 友好型视角

> 审查日期：2026-05-24
> 审查范围：Genesis 物理引擎 v0.2.x 全量 API 面
> 审查目标：评估 Genesis API 对 LLM/Agent 代码生成的友好程度，识别系统性缺陷

---

## 执行摘要

Genesis 是一个功能强大的通用物理引擎，但其 API 设计在 **Agent 友好型** 方面存在显著缺陷。本报告基于两项系统性审查——(1) 全量 API 面审查，覆盖命名、注册模式、参数设计、默认值、约束关系、错误信息、重载使用 7 个维度；(2) 错误信息与可发现性专项审查——共识别 **56 个具体问题**。

核心发现：Genesis API 中有大量"隐藏秘密"——无法从参数名或文档推断的关键方法名、必须在特定对象上调用而非直接构造的注册步骤、必须同时满足的数学约束。这类 API 对 LLM 代码生成极其不利，直接导致我们在 benchmark 中 Drone/Sensor/Terrain 三个域的成功率仅 12%-25%。

---

## 1. 评估框架：什么是 Agent 友好型 API

一个 Agent 友好型 API 满足以下 6 条原则：

| # | 原则 | 含义 |
|---|------|------|
| P1 | **单次调用构造** | 创建+注册一步完成，不需要在多个对象上依次调用 |
| P2 | **可推断命名** | 方法名、参数名遵循一致约定，不能有拼写错误或非标准缩写 |
| P3 | **独立参数** | 每个参数可独立设置，不需要跨参数协调才能通过验证 |
| P4 | **直觉默认值** | 默认值的语义和量级符合直觉，1 就是 1 米，不是 200 |
| P5 | **自描述错误** | 错误信息包含"你传了什么、应该传什么、可选值有哪些" |
| P6 | **可发现性** | 实体/类型/参数的可选值可通过 API 查询，不依赖阅读源码 |

针对 LLM 代码生成的特殊性：
- LLM **不会**读取源码，它只看系统提示词和 API 签名
- LLM **逐个参数独立推理**，无法同时满足多个跨参数约束
- LLM 对**默认值的语义**完全依赖参数名猜测

---

## 2. 问题总览

按影响级别分类：

| 影响级别 | 数量 | 典型表现 |
|---------|------|---------|
| **严重** — 直接导致代码无法运行 | 23 | 方法名拼写错误、注册步骤缺失、参数格式不对 |
| **中等** — 运行时异常但可通过试错修复 | 21 | 默认值不合理、缺少可选值提示、互斥参数 |
| **轻微** — 非致命但增加认知负担 | 12 | 命名不一致、文档缺失、重载滥用 |

按缺陷类别分类：

| 类别 | 严重 | 中等 | 轻微 | 合计 |
|------|------|------|------|------|
| 命名违规 | 6 | 1 | 1 | 8 |
| 多阶段注册 | 4 | 1 | 0 | 5 |
| 索引式参数 | 4 | 1 | 0 | 5 |
| 反直觉默认值 | 2 | 5 | 2 | 9 |
| 参数相互依赖 | 5 | 4 | 1 | 10 |
| 错误信息缺失 | 1 | 6 | 3 | 10 |
| 重载/别名滥用 | 1 | 3 | 5 | 9 |

---

## 3. 详细发现

### 3.1 命名违规（8 项）

**严重：拼写错误在公开 API 中**

| 位置 | 现状 | 问题 |
|------|------|------|
| `Drone.set_propellels_rpm()` | `propellels`（多一个 `el`） | LLM 生成 `set_propeller_rpm()`、`set_propellers_rpm()` 均失败 |
| `gs.sensors` 模块 | `Lidar` 是 `Raycaster` 的别名 | LLM 不知道该用哪个，两个名字指向同一个类 |
| `gs.materials.FEM.Cloth` | 类名 `Cloth` 但底层是 FEM 薄壳 | LLM 可能尝试找 `gs.materials.Cloth` |

**严重：命名约定不一致**

| 位置 | 不一致 |
|------|--------|
| `gs.morphs.Terrain` | `horizontal_scale` 和 `vertical_scale` 一个是形容词一个是名词形式 |
| `gs.sensors.IMU` | `acc_noise` 和 `gyro_noise` 缩写风格不统一 |
| `gs.morphs.Box` vs `gs.morphs.Sphere` | `size=(x,y,z)` vs `radius=r` —— 同是基本几何体，参数名完全不同 |

**中等：非标准缩写**

| 位置 | 缩写 | 影响 |
|------|------|------|
| `entity.idx` | `idx` 不是 `id` 或 `index` | LLM 参考其他引擎会写 `entity.id` |
| `link.idx_local` | `idx_local` 含下划线但 `idx` 无前缀 | 组合使用时常写错 |

### 3.2 多阶段注册（5 项）

这是 Genesis API 最严重的 Agent 友好性问题。**构造对象和注册对象是两个独立步骤**，但 LLM 天然认为"调用构造函数后对象已可用"。

**严重：传感器两段式 API**

```python
# ❌ LLM 的自然写法（100% 幻觉率）
imu = gs.sensors.IMU(entity="robot", pose=(0,0,0))  # 参数名全错
data = imu.read()

# ✅ 正确写法（5 步）
opts = gs.sensors.IMU(entity_idx=robot.idx, link_idx_local=link.idx_local)
sensor = scene.add_sensor(opts)  # 这一步 LLM 永远猜不到
scene.build()
scene.step()
data = sensor.read()
```

**影响**：Sensor 域 Stage 1 成功率仅 2/8 (25%)。

**严重：相机两套 API 并存**

```python
# 方式 A：scene.add_camera() — 旧版，直接在 scene 上构造
# 方式 B：gs.sensors.Camera() + scene.add_sensor() — 新版传感器模式
```

`add_camera()` 作为旧版便捷方法仍然存在，但功能受限。LLM 可能混用两套 API 的参数。

**中等：力场构造后需 scene.add_entity() 包装**

力场 (`gs.force_fields.*`) 不是独立实体，需要附着在 `gs.morphs.ForceField` 实体上才能生效。这个间接层次对 LLM 完全不可见。

### 3.3 索引式参数（5 项）

**严重：实体引用使用整数索引而非名称**

```python
# ❌ LLM 期望的（名称引用）
sensor_opts = gs.sensors.IMU(entity="robot", link="end_effector")

# ✅ Genesis 实际要求（整数索引）
sensor_opts = gs.sensors.IMU(entity_idx=robot.idx, link_idx_local=link.idx_local)
```

字符串名称是业界标准（MuJoCo、Isaac Sim、PyBullet 均如此）。要求整数索引 + 必须从 entity 对象上取 `.idx` 属性，对 LLM 极不友好。

**严重：受力查询使用整数索引**

```python
# force = entity.get_force()          # ❌ 不存在
force = scene.sim.rigid_solver.entities[entity.idx].get_force()  # ✅
```

**中等：材质/表面的实体关联**

材质和表面在 `scene.add_entity()` 时通过参数传入，但如果需要运行时修改，又需要通过 `entity.idx` 去 solver 内部查找，API 前后不一致。

### 3.4 反直觉默认值（9 项）

**严重：vertical_scale=0.005 导致高度语义断裂**

```python
# Terrain 默认 vertical_scale=0.005
# 高度场值 200 → 实际高度 1 米
# LLM 写 height_field 的值时完全不知所措
```

**严重：hover RPM = 14468.429183500699**

无人机悬停需要这个精确的魔术数字，没有任何 API 暴露该值，LLM 无法推理。

**中等：substeps 默认值**

| solver | 默认 substeps | 影响 |
|--------|-------------|------|
| Rigid | 1 | 高速碰撞穿透 |
| MPM | 10 | 用户不知为何和 Rigid 不同 |
| FEM | 5 | 同上 |

LLM 不知道何时该调整 substeps，默认值差异也没有文档说明原因。

**中等：FEM 材料参数非物理直觉**

```python
gs.materials.FEM.Elastic(
    youngs_modulus=1e6,    # 默认值，但 LLM 可能设 1e9（金属级）导致爆炸
    poissons_ratio=0.3,     # 泊松比，非材料科学背景的 LLM 不理解范围 [0, 0.5]
)
```

**轻微：randomize 默认 False**

Terrain 的 `randomize` 默认为 `False`，但 LLM 调用 `random_uniform_terrain` 时自然期望每次不同——结果每次生成相同地形。

### 3.5 参数相互依赖（10 项）

**严重：Terrain 参数整除约束**

```python
# 运行时检查：subterrain_size / horizontal_scale 必须整除
terrain = gs.morphs.Terrain(
    n_subterrains=(2, 2),
    subterrain_size=(6.0, 6.0),
    horizontal_scale=0.25,   # 6.0 / 0.25 = 24 ✓
)
# 如果 horizontal_scale=0.3 → 6.0/0.3=20.0 ✓
# 如果 horizontal_scale=0.33 → 6.0/0.33=18.18... → 运行时异常
```

LLM 逐个参数独立选择，无法验证整除关系。

**严重：subterrain_types 形状约束**

```python
n_subterrains=(2, 2)
# subterrain_types 必须是 2×2 嵌套列表：
subterrain_types=[["flat", "hilly"], ["slope", "discrete"]]
# LLM 常写成:
subterrain_types=["flat", "hilly"]           # 一维列表，形状不匹配
subterrain_types="hilly_terrain"             # 字符串，类型不匹配
```

**严重：height_field vs subterrain 互斥**

```python
# 两种模式互斥，混合参数被静默忽略：
gs.morphs.Terrain(height_field=hf)           # 模式 1：n_subterrains 忽略
gs.morphs.Terrain(n_subterrains=(2,2))       # 模式 2：height_field 必须为 None
```

**中等：Drone URDF 路径和 model 字段冲突**

```python
gs.morphs.Drone(file="urdf/drones/cf2x.urdf")  # file= 指定 URDF
gs.morphs.Drone(model="CF2X")                    # model= 从内置列表选择
# 两个参数不应该同时提供，但缺少互斥检查
```

**中等：Rigid 的质量 vs 密度**

```python
# Rigid 材质可以通过 rho（密度）或直接质量影响物理
# 但质量 = rho × 体积，LLM 很难心算组合是否正确
gs.materials.Rigid(rho=1000)  # 密度方式
# 没有直接的 mass= 参数
```

### 3.6 错误信息缺失（10 项）

**严重：不提供可选项列表**

```python
# 传了无效的资产路径时的错误：
# "File not found: urdf/robot.urdf"  ← 不告诉你去哪找

# 传了无效的 subterrain_types 时的错误：
# "ValueError"  ← 不列出 10 种合法类型
```

**中等：裸 NotImplementedError**

多处 `raise NotImplementedError` 没有附带消息，Agent 看到后不知道是什么功能没实现：

```python
# genesis/engine/entities/__init__.py 等多处
raise NotImplementedError  # 无消息文本
```

**中等：属性错误不提供有效属性列表**

```python
# entity.xxx 拼错时：
# "AttributeError: 'RigidEntity' object has no attribute 'get_vel'"
# 应提示 "Did you mean: get_velocity()?"
```

**中等：错误消息中的信息不一致**

不同模块的同类错误格式不同。例如 build() 后的注册错误 vs build() 后的修改错误，有的给出方法名，有的只给类型名。

**轻微：系统级错误被直接抛出**

GPU/CUDA 初始化失败时，Genesis 直接抛出底层 CUDA 异常，不包装为 "Genesis requires CUDA 11.x+, detected: ..." 的友好提示。

### 3.7 重载/别名滥用（9 项）

**严重：同一类多个名称**

```python
gs.sensors.Lidar       # = gs.sensors.Raycaster
gs.sensors.DepthCamera # = gs.sensors.Raycaster 的子类
gs.sensors.Camera      # 又是另一种传感器
```

LLM 不知道这三个名字之间的关系，也不知道何时该用哪个。

**中等：同一功能多种调用路径**

```python
# 添加几何体：
scene.add_entity(morph=gs.morphs.Box(...))
scene.add_entity(gs.morphs.Box(...))         # morph= 可省略

# 添加相机（三套 API）：
scene.add_camera(...)                         # 旧版便捷方法
camera = gs.sensors.Camera(...)              # Options 构造
scene.add_sensor(camera)                     # 传感器注册
```

**中等：参数传递位置和关键字混用**

```python
# scene.add_entity() 接受:
scene.add_entity(morph, material, surface)        # 位置参数
scene.add_entity(morph=morph, material=mat)       # 关键字参数
scene.add_entity(entity)                          # 直接传 Entity 对象？不存在
```

---

## 4. 错误信息专项审计

对 Genesis 错误处理机制的全面审查发现以下系统性问题：

### 4.1 错误信息质量分布

| 错误类型 | 有信息 | 无信息/裸异常 | 含修复提示 |
|---------|--------|-------------|----------|
| 参数验证 | 部分 | 少数 | 极少 |
| 资产加载 | 有路径无建议 | 无 | 无 |
| build() 时序 | 有 | 无 | 无 |
| 运行时类型错误 | 有类型无期望 | 无 | 无 |
| GPU/CUDA | 无 | 全部 | 无 |

### 4.2 资产可发现性为零

Genesis 有内置资产目录 (`genesis/assets/`)，包含 URDF 机器人、MJCF 模型、纹理等。但：

- 没有 `genesis.list_assets()` 或 `scene.list_available_models()` API
- `get_assets_dir()` 函数存在于 `genesis.utils` 但未在 `__init__.py` 中导出
- 资产路径规则（相对路径 → 先找当前目录，再找 assets 目录）没有在任何 API 文档中说明
- LLM 只能靠训练数据中碰巧见过的路径（如 `"urdf/drones/cf2x.urdf"`）来猜测

### 4.3 错误消息中的复制粘贴错误

发现多处错误消息明显是从其他类复制后未修改：

- 某类的参数验证报错提到的是另一个类的属性名
- solver 类型错误中混用了 rigid_solver 和 mpm_solver 的名称

---

## 5. 对 Benchmark 结果的量化影响

基于 `stage1_prompts.json` 100 个提示词的 golden 覆盖率分析：

| 域 | 成功率 | 主要绊脚石 | 对应缺陷类别 |
|---|--------|----------|------------|
| Drone | 1/8 (12%) | 拼写错误的方法名 + 魔术数字 | 命名违规, 反直觉默认值 |
| Sensor | 2/8 (25%) | 两段式注册 + 整数索引 | 多阶段注册, 索引式参数 |
| Terrain | 1/8 (12%) | 整除约束 + 形状匹配 | 参数相互依赖, 反直觉默认值 |
| FEM Cloth | 3/8 (38%) | Box 做布料不合直觉 | 重载滥用 |
| MPM Sand | 4/7 (57%) | 材质参数不熟悉 | 反直觉默认值 |

**三个最差域的失败原因 100% 可归因到本报告中的 API 设计问题。**

---

## 6. 改进建议

### 6.1 立即可行的 RAG 侧缓解（不修改 Genesis 源码）

| 措施 | 目标问题 | 预期效果 |
|------|---------|---------|
| 在系统提示词中嵌入完整可运行代码骨架 | 多阶段注册、魔术数字 | Drone/Sensor/Terrain 成功率 +30-50% |
| 维护 API 签名 → 正确用法的映射 KB | 命名违规、索引参数 | 减少幻觉 API 调用 70% |
| 添加"常见错误"反例到约束库 | 参数依赖、默认值 | 约束命中率提升 |

### 6.2 Genesis API 改进建议（需修改源码）

**高优先级（影响大、改动小）：**

1. **添加 `Drone.hover_rpm` 属性** — 一行代码，暴露悬停 RPM 值
2. **`subterrain_types` 验证时列出 10 种合法类型** — 修改错误消息字符串
3. **`entity_idx` 接受字符串名称** — 内部查表转换，向下兼容
4. **为 `set_propellels_rpm` 添加拼写正确的别名** `set_propeller_rpm`
5. **添加 `scene.list_available_models()` 资产发现 API**

**中优先级（影响大、改动中等）：**

6. **传感器单步构造** — `scene.add_sensor()` 同时接受 Options 对象和直接参数
7. **参数验证错误统一为 "you passed X, expected one of [A, B, C]" 格式**
8. **`vertical_scale` 默认值改为 1.0 或添加 `height_scale` 别名**

**低优先级（长期改进）：**

9. **统一命名约定** — `idx` → `index`, `rho` → `density`, 消除拼写错误
10. **消除别名** — 废弃 `gs.sensors.Lidar`，统一为 `gs.sensors.Raycaster`

---

## 7. 总结

Genesis 的 API 设计呈现一个清晰的模式：**面向人类专家的代码示例驱动 API vs 面向 LLM Agent 的推理驱动 API 之间的鸿沟**。

人类专家通过阅读 `examples/` 目录下的完整脚本学习 API——他们看到完整的 5 步传感器注册流程、hover RPM 的具体数值、terrain 参数的整除关系。LLM 没有这个能力——它只能从 API 签名和参数名推断用法。

核心矛盾在于：**Genesis 中大量"从示例中学习"的知识，无法通过 API 签名本身传递**。对于人类这是合理的设计（示例文档完善），对于 LLM 这是灾难（签名完全不可推断）。

改进路径有两种：一是在 RAG 层面补齐——将示例代码、约束规则、反例打包进检索库和系统提示词；二是在 API 层面简化——减少注册步骤、增强自描述性、改善错误信息。两种路径互补，本报告为两种路径都提供了具体的行动项。

---

*本报告基于对 Genesis 源码的全面审计，结合 100 个 benchmark 提示词的量化实验结果。审查覆盖 `genesis/options/`、`genesis/engine/`、`genesis/sensors/` 等核心模块的完整 API 面。*

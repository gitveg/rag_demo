# Stage 1 低成功率域分析：Drone / Sensor / Terrain

当前 Stage 1 Prompt 数据集的 golden `expected_apis` 覆盖率为 56/100，其中三个域严重拖后腿：

| 域 | 成功率 | golden 数 |
|---|---|---|
| Drone | 1/8 (12%) | 1 |
| Sensor | 2/8 (25%) | 2 |
| Terrain | 1/8 (12%) | 1 |

本文档结合 Genesis 源码分析根因，并提出改进方向。

---

## 1. Drone（1/8）— 唯一的控制入口无法推理

### Genesis 无人机控制真面目

Genesis Drone 只有一个控制方法：

```python
drone.set_propellels_rpm([rpm0, rpm1, rpm2, rpm3])
```

注意方法名有拼写错误（`propellels` 多了一个 `el`）。无人机通过 4 个电机的 RPM 来控制——没有 `apply_force()`，没有 `set_vel()`，没有 `set_pos()`。

悬停需要精确的魔术数字：

```python
hover_rpm = 14468.429183500699   # cf2x 的悬停 RPM
```

任何非平凡飞行的正确控制链路是 **3 层 PID 级联 + 电机混控器**：

```
目标位置 → PID位置(3个) → PID速度(3个) → PID姿态(3个) → 混控矩阵 → set_propellels_rpm()
```

混控矩阵（X 型四旋翼布局）：
```python
M1 = base_rpm + thrust - roll - pitch - yaw
M2 = base_rpm + thrust - roll + pitch + yaw
M3 = base_rpm + thrust + roll + pitch - yaw
M4 = base_rpm + thrust + roll - pitch - yaw
```

完整代码参考：`examples/drone/quadcopter_controller.py`

### LLM 实际生成了什么

```
幻觉方法：drone.apply_force(), drone.set_vel(), drone.set_pos(), drone.apply_external_force()
幻觉属性：drone.get_mass(), drone.get_ang()
替代方案：用 gs.morphs.Box 代替 Drone + PID 调位置（跟无人机 API 完全无关）
```

### 根因

`set_propellels_rpm` 这个 API 名称、hover RPM 值、PID 级联控制链——**每一项都无法从 API 名称或文档推断**。LLM 只能从训练数据或系统提示词中直接获取完整代码模板。

### 改进方向

在 query_gen 生成提示词中嵌入完整的最小工作示例：
```python
# 最小悬停骨架
drone = scene.add_entity(gs.morphs.Drone(file="urdf/drones/cf2x.urdf", pos=(0,0,1.0)))
scene.build()
hover_rpm = 14468.429183500699
for _ in range(N):
    drone.set_propellels_rpm([hover_rpm] * 4)
    scene.step()
```

---

## 2. Sensor（2/8）— 附着机制完全不符合直觉

### Genesis 传感器的真实用法

传感器生命周期是 **5 步**：

```python
# Step 1: 构造 Pattern（仅 Lidar/DepthCamera 需要）
pattern = gs.sensors.SphericalPattern(fov=(360.0, 60.0), n_points=(128, 64))

# Step 2: 构造 Options（仅创建配置对象，不是最终 API）
sensor_opts = gs.sensors.Lidar(
    pattern=pattern,                   # Lidar/DepthCamera 必需
    entity_idx=robot.idx,              # 全局实体索引（整数）
    link_idx_local=link.idx_local,     # 局部连杆索引（整数）
    pos_offset=(0.3, 0.0, 0.1),       # 附着偏移
)

# Step 3: 通过 scene.add_sensor() 注册（必须在 build 前）
sensor = scene.add_sensor(sensor_opts)

# Step 4: 构建场景
scene.build()

# Step 5: 每步读取数据
scene.step()
data = sensor.read()  # RaycasterData(points, distances) 或 IMUData(lin_acc, ang_vel)
```

关键事实：
- `gs.sensors.Lidar` 是 `gs.sensors.Raycaster` 的别名
- `DepthCamera` 是 `Raycaster` 的子类，额外提供 `read_image()` 方法
- IMU 数据字段是 `.lin_acc` 和 `.ang_vel`
- `entity_idx` 是全局实体索引（`entity.idx`），不是字符串
- `link_idx_local` 是局部连杆索引（`link.idx_local`），不是字符串

### LLM 实际生成了什么

```
幻觉模式1：在 Options 上设 pose/entity
    gs.sensors.Lidar(entity="robot", pose=(0,0,0))
    → entity= 和 pose= 不存在

幻觉模式2：跳过 scene.add_sensor()
    imu = gs.sensors.IMU(noise=0.1, attach_to="end_effector")
    → 构造了 Options，但从未注册到场景

幻觉模式3：忘记 Pattern 对象
    gs.sensors.Lidar(fov=60)
    → fov 不是直接参数，需包在 SphericalPattern 里

幻觉模式4：编造不存在参数
    entity=, pose=, attach_to=, noise=(单一值，实际需要 acc_noise+gyro_noise 分开)
```

### 根因

**两段式 API 设计是逆直觉的**：先 `gs.sensors.XXX()` 构造 Options，再 `scene.add_sensor()` 注册——LLM 天然认为"调用了 `gs.sensors.Lidar()` 就算创建了传感器"。加上 `entity_idx`/`link_idx_local` 需要实体索引而非名称，Pattern 对象需要预构造——这些都无法从 API 表面推断。

### 改进方向

在系统提示词中嵌入三种传感器的完整最小工作示例（Lidar、DepthCamera、IMU），显式标注 **"Options 只是配置，必须通过 scene.add_sensor() 注册"**。

---

## 3. Terrain（1/8）— 参数约束链太复杂

### Genesis Terrain 的真实用法

两种模式互斥：

**模式 A：程序化子地形（subterrain）**
```python
terrain = scene.add_entity(
    gs.morphs.Terrain(
        n_subterrains=(2, 2),
        subterrain_size=(6.0, 6.0),
        horizontal_scale=0.25,
        vertical_scale=0.005,
        subterrain_types=[
            ["flat_terrain", "random_uniform_terrain"],
            ["pyramid_sloped_terrain", "discrete_obstacles_terrain"],
        ],
    ),
)
# 无需 material= — Terrain 自动是 fixed rigid body
```

**模式 B：高度场数组**
```python
import numpy as np
hf = np.zeros([40, 40])
hf[10:30, 10:30] = 100
terrain = scene.add_entity(
    gs.morphs.Terrain(
        horizontal_scale=0.25,
        vertical_scale=0.005,
        height_field=hf,   # 必须是 np.ndarray，2D
    ),
)
# n_subterrains / subterrain_size / subterrain_types 在 height_field 模式下全部忽略
```

**模式 C：Mesh 文件转高度场**
```python
from genesis.utils.terrain import mesh_to_heightfield
hf, xs, ys = mesh_to_heightfield("path/to/terrain.obj", spacing=0.25)
# 然后按模式 B 使用 hf
```

关键约束：
- `subterrain_size` 必须能被 `horizontal_scale` 整除，否则运行时异常
- `subterrain_types` 如果是二维列表，形状必须精确匹配 `n_subterrains`
- `vertical_scale` 默认是 `0.005`——高度值 200 才 = 1 米，LLM 对此没有概念
- `randomize` 默认为 `False`，每次生成相同地形（seed=0）

### LLM 实际生成了什么

| 错误类型 | LLM 的幻觉 | 正确 API |
|---|---|---|
| 参数名 | `height_scale=`, `terrain_config=`, `mesh=`, `subterrains=` | `vertical_scale=`, 其他不存在 |
| height_field 类型 | `lambda x,y: ...` | 必须是 `np.ndarray` |
| subterrain_types 格式 | `"hilly_terrain"`, `"mountain"` | 只能从 10 种类型中选 |
| subterrain_types 形状 | `["type_a", "type_b"]` 一维 | 必须匹配 `n_subterrains` 的 (rows, cols) |
| 缺少必需参数 | 省略 `horizontal_scale` | 必须提供，否则整除检查失败 |

### 根因

Terrain 的参数之间有多重相互约束（整除、形状匹配、互斥），LLM 逐个参数独立猜测，无法满足全局一致性。加上 `vertical_scale=0.005` 的默认值让高度语义变得反直觉，LLM 写 `height_field` 的值时完全不知所措。

### 改进方向

在系统提示词中：
1. 给出完整的两个模式代码示例
2. 显式列出 10 种合法的 `subterrain_types` 字符串
3. 标注参数约束（整除、形状匹配、互斥关系）
4. 解释 `vertical_scale` 和实际高度的映射关系

---

## 总结

| 域 | 核心问题 | 改进手段 |
|---|---|---|
| **Drone** | 控制方法名+魔术数字+3层PID 无法推理 | 嵌入完整悬停/飞行代码骨架 |
| **Sensor** | 两段式 API（Options + add_sensor）违反直觉 | 嵌入三种传感器的最小工作示例 |
| **Terrain** | 多参数间约束链复杂，LLM 无法满足全局一致性 | 嵌入两种模式的完整代码+约束标注 |

三个域的共同特征：**API 设计有"隐藏秘密"**——一个无法从参数名或文档推断的关键方法名、一个必须在特定对象上调用而非直接构造的注册步骤、一组必须同时满足的数学约束。对于这种 API，参数列表式提示词不够，需要**完整可运行的代码骨架**让 LLM 填充业务逻辑。

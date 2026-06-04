"""
benchmark/query_gen.py
======================
读取 query JSON 中的每条 query，用 LLM（OpenAI 兼容接口，见 .env 的 CHAT_API_KEY）
生成 Genesis 脚本，写入 benchmark/results/tests/query_{number}.py，执行验证；失败则最多重试 3 次。
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

from openai import OpenAI
from tqdm import tqdm
import dotenv

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_BENCHMARK_DIR = _SCRIPTS_DIR  # 脚本直接放在 benchmark/ 下，与 phys_agent/benchmark/scripts/ 不同
_PROJECT_ROOT = os.path.dirname(_BENCHMARK_DIR)

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

dotenv.load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
dotenv.load_dotenv(os.path.join(_BENCHMARK_DIR, ".env"))

DEFAULT_QUERY_JSON = os.path.join(_BENCHMARK_DIR, "query.json")
QUERY_TESTS_DIR = os.path.join(_BENCHMARK_DIR, "results", "tests")
RUN_TIMEOUT = 600

GEN_MODEL = "gpt-5.4"
EXTRACT_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

EXCLUDED_APIS = {"genesis.init", "genesis.cpu", "genesis.gpu", "genesis.cuda"}
EXCLUDED_API_PREFIXES = ("genesis.logging",)


def _get_chat_client() -> OpenAI:
    key = os.getenv("CHAT_API_KEY")
    if not key:
        raise ValueError("请在 rag_demo/.env 中设置 CHAT_API_KEY")
    return OpenAI(
        api_key=key,
        base_url=os.getenv("CHAT_API_BASE_URL", "https://api.chatanywhere.tech/v1"),
    )


def _get_deepseek_client() -> OpenAI:
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise ValueError("请在 rag_demo/.env 中设置 DEEPSEEK_API_KEY")
    return OpenAI(
        api_key=key,
        base_url=os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com"),
    )


def _strip_code_fences(text: str) -> str:
    t = (text or "").strip()
    t = re.sub(r"^```(?:python|py)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```\s*$", "", t)
    return t.strip()


def _extract_query_number(task_id: str, fallback_idx: int) -> int:
    m = re.search(r"(\d+)$", str(task_id))
    if m:
        return int(m.group(1))
    return fallback_idx + 1


def _query_file_path(task_id: str, fallback_idx: int) -> str:
    os.makedirs(QUERY_TESTS_DIR, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", task_id)
    return os.path.join(QUERY_TESTS_DIR, f"{safe}.py")


def generate_code(client: OpenAI, user_query: str, task_id: str) -> str:
    system = """你是 Genesis 物理引擎专家。根据用户指令生成完整可运行的 Python 脚本。

=== 代码结构要求 ===
- 使用 import genesis as gs；
- 包含 gs.init、Scene、add_entity、scene.build、必要仿真循环；
- 代码应能在本机 Genesis 环境中执行；
- 只输出 Python 源码，不要 Markdown 代码围栏。

=== 生命周期规则（严格遵守）===
- gs.init() 必须最早调用。
- scene.add_entity()、scene.add_camera()、scene.start_recording() 必须在 scene.build() 之前。
- scene.build() 之后才能 scene.step()。
- 不要在 build() 之后添加实体、相机或开启录制。
- 禁止使用 show_viewer=True（headless 执行会崩溃）。Gs.Scene() 中不要传 show_viewer 参数。

=== 几何体选择规则 ===
优先使用程序化几何体（无需文件路径，始终可用）：
  gs.morphs.Plane()                        —— 无限地面
  gs.morphs.Box(pos=(x,y,z), size=(w,h,d)) —— 立方体
  gs.morphs.Sphere(pos=(x,y,z), radius=r)   —— 球体
  gs.morphs.Cylinder(pos=(x,y,z), radius=r, height=h) —— 圆柱体
除非用户明确要求特定模型文件，不要使用 Mesh/URDF/MJCF/Drone。

=== 材质规则 ===
  gs.materials.Rigid(rho=密度默认200.0, friction=摩擦系数[1e-2,5.0], coup_friction=0.1, coup_restitution=0.0)
  注意：Rigid 没有 restitution 参数，弹性恢复系数是 coup_restitution。
  gs.materials.FEM.Cloth(rho=0.5, E=5e4, nu=0.49, thickness=0.001, model="stable_neohookean")
  gs.materials.FEM.Elastic(rho=1000.0, E=1e5, nu=0.2, model="linear")
  注意：FEM 材料参数名是 rho(非density)、E(非youngs_modulus)、nu(非poissons_ratio)。
  gs.materials.SPH.Liquid(sampler="regular")
  gs.materials.MPM.Sand(sampler="regular")

=== 表面外观规则 ===
  gs.surfaces.Default(color=(r, g, b, 1.0))
  gs.surfaces.Rough(color=(r, g, b, 1.0))
  gs.surfaces.Glass(color=(r, g, b, 0.5))
  gs.surfaces.Gold(color=(1.0, 0.84, 0.0, 1.0))
  gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0))
  gs.surfaces.Aluminium(color=(0.9, 0.9, 0.9, 1.0))
  gs.surfaces.Emission(color=(r, g, b, 1.0))

=== 渲染器规则 ===
  gs.options.renderers.RayTracer()          —— 高质量光线追踪
  gs.options.renderers.Rasterizer()         —— 快速光栅化

=== 力场规则 ===
  注意：力场 API 在 gs.force_fields 下，不是 gs.options.ForceField。
  scene.add_force_field(gs.force_fields.Constant(direction=(x,y,z), strength=s))
  scene.add_force_field(gs.force_fields.Turbulence(strength=s, frequency=f))
  scene.add_force_field(gs.force_fields.Vortex(direction=(x,y,z), strength_perpendicular=s))
  scene.add_force_field(gs.force_fields.Noise(strength=s))

=== 如果需要导入外部模型文件 ===
已知可用的资产路径（相对于 Genesis assets 目录）：
  # URDF 机器人
  "urdf/panda_bullet/panda.urdf"            —— Franka Panda 机械臂
  "urdf/go2/urdf/go2.urdf"                  —— Unitree Go2 四足机器人
  "urdf/anymal_c/urdf/anymal_c.urdf"        —— ANYmal C 四足机器人
  "urdf/shadow_hand/shadow_hand.urdf"       —— Shadow 灵巧手
  "urdf/kuka_iiwa/model.urdf"               —— KUKA iiwa 机械臂
  "urdf/simple/two_link_arm.urdf"           —— 简单双连杆臂
  # MJCF 机器人（.xml 扩展名）
  "xml/franka_emika_panda/panda.xml"        —— Franka Panda（最常用）
  "xml/universal_robots_ur5e/ur5e.xml"      —— UR5e 机械臂
  "xml/ant.xml"                             —— 四足蚂蚁机器人
  "xml/humanoid.xml"                        —— 人形机器人
  # Drone（仅 .urdf，需指定 model 参数）
  gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X")     —— Crazyflie 2.X
  gs.morphs.Drone(file="urdf/drones/cf2p.urdf", model="CF2P")     —— Crazyflie 2.P
  gs.morphs.Drone(file="urdf/drones/racer.urdf", model="RACE")    —— Racer 竞速无人机
  # Mesh 模型
  "meshes/bunny.obj"                        —— 斯坦福兔子
  "meshes/dragon.obj"                       —— 斯坦福龙
  "meshes/duck.obj"                         —— 鸭子
  "meshes/sphere.obj"                       —— 球体网格
  "meshes/cloth.obj"                        —— 布料网格
  "meshes/tank.obj"                         —— 坦克模型
  "meshes/boat/boat.obj"                    —— 船模型
  "meshes/terrain_45.obj"                   —— 斜坡地形

=== 无人机（Drone）控制规则 ===
Drone 只有一个控制方法，注意方法名有拼写错误（propellels 多一个 "el"）：
  drone.set_propellels_rpm([rpm0, rpm1, rpm2, rpm3])

CF2X 悬停 RPM 精确值：14468.429183500699（无 API 可查询，必须直接用此魔术数字）

X 型四旋翼混控公式（M1=右前, M2=左前, M3=左后, M4=右后）：
  M1 = hover_rpm + thrust - roll - pitch - yaw
  M2 = hover_rpm + thrust - roll + pitch + yaw
  M3 = hover_rpm + thrust + roll + pitch - yaw
  M4 = hover_rpm + thrust + roll - pitch - yaw

最简悬停骨架（可直接复制后修改业务逻辑）：
```python
drone = scene.add_entity(gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X", pos=(0, 0, 0.5)))
scene.build()
hover_rpm = 14468.429183500699
for _ in range(500):
    drone.set_propellels_rpm([hover_rpm, hover_rpm, hover_rpm, hover_rpm])
    scene.step()
```

简化高度控制（P 控制器，目标高度=target_z）：
```python
target_z = 1.0
# --- 在仿真循环内 ---
current_z = drone.get_pos()[2]
error = target_z - current_z
adjusted = hover_rpm + error * 5000.0
drone.set_propellels_rpm([adjusted, adjusted, adjusted, adjusted])
```

水平运动：通过差速产生倾斜姿态。前进(+x)时减少前两电机、增加后两电机 RPM；同理左右移动。

=== 传感器（Sensor）规则 ===
传感器生命周期为严格 5 步，不能跳过：
  Step 1: 构造 Pattern（仅 Lidar/DepthCamera 需要，IMU 不需要）
  Step 2: 构造 Options（注意参数名 entity_idx / link_idx_local，不要写 entity / attach_to）
  Step 3: scene.add_sensor(options) 注册（必须在 build 前！）
  Step 4: scene.build()
  Step 5: sensor.read() 读取数据

IMU 完整骨架（不需要 Pattern）：
```python
robot = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
# entity_idx 是 entity.idx（整数），不是字符串名称
imu_opts = gs.sensors.IMU(
    entity_idx=robot.idx,
    link_idx_local=0,
    pos_offset=(0.0, 0.0, 0.1),
    acc_noise=0.01,
    gyro_noise=0.001,
)
imu = scene.add_sensor(imu_opts)
scene.build()
for _ in range(500):
    scene.step()
    data = imu.read()  # data.lin_acc (3,), data.ang_vel (3,)
```

Lidar 完整骨架（需要 Pattern）：
```python
pattern = gs.sensors.SphericalPattern(fov=(360.0, 30.0), n_points=(360, 16))
lidar_opts = gs.sensors.Lidar(
    pattern=pattern,
    entity_idx=robot.idx,
    link_idx_local=0,
    pos_offset=(0.0, 0.0, 0.3),
)
lidar = scene.add_sensor(lidar_opts)
scene.build()
for _ in range(500):
    scene.step()
    data = lidar.read()  # data.points (N,3), data.distances (N,)
```
DepthCamera 完整骨架（需要 DepthCameraPattern，参数与 Lidar 不同）：
```python
pattern = gs.sensors.DepthCameraPattern(res=(640, 480), fov_horizontal=60.0)
depth_opts = gs.sensors.DepthCamera(
    pattern=pattern,
    entity_idx=robot.idx,
    link_idx_local=0,
    pos_offset=(0.0, 0.0, 0.1),
)
depth_cam = scene.add_sensor(depth_opts)
scene.build()
for _ in range(500):
    scene.step()
    data = depth_cam.read()        # data.distances (N,), data.points (N,3)
    depth_img = depth_cam.read_image()  # (H, W) depth map as torch.Tensor
```

=== 地形规则 ===
Terrain 有两种互斥模式，一个 scene 只能选一种：

模式 A：程序化子地形
```python
terrain = scene.add_entity(gs.morphs.Terrain(
    pos=(0, 0, 0),
    n_subterrains=(2, 2),                  # (x方向, y方向)
    subterrain_size=(6.0, 6.0),            # 每个子地形大小(米)，必须能被 horizontal_scale 整除
    horizontal_scale=0.25,                 # 网格精度：6.0/0.25=24 整除 ✓
    vertical_scale=0.005,                  # 高度单位换算：值200才=1米
    subterrain_types=[                     # 形状必须匹配 n_subterrains
        ["flat_terrain", "fractal_terrain"],
        ["sloped_terrain", "wave_terrain"],
    ],
))
```
如果只用一种地形类型，可用字符串简写：subterrain_types="fractal_terrain"

模式 B：高度场（与模式 A 互斥，有 height_field 则 n_subterrains 参数忽略）
```python
import numpy as np
hf = np.zeros((40, 40))
hf[10:30, 10:30] = 200  # vertical_scale=0.005 时，200 → 1 米高
terrain = scene.add_entity(gs.morphs.Terrain(
    horizontal_scale=0.25,
    vertical_scale=0.005,
    height_field=hf,                        # 必须是 np.ndarray 二维数组
))
```

合法 subterrain_types 共 10 种：
  flat_terrain, fractal_terrain, random_uniform_terrain, sloped_terrain,
  pyramid_sloped_terrain, discrete_obstacles_terrain, wave_terrain,
  stairs_terrain, pyramid_stairs_terrain, stepping_stones_terrain"""
    user = f"task_id: {task_id}\n\n用户指令：\n{user_query}"
    resp = client.chat.completions.create(
        model=GEN_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2,
    )
    raw = (resp.choices[0].message.content or "").strip()
    return _strip_code_fences(raw)


def extract_apis_from_code(code: str, task_id: str) -> List[str]:
    client = _get_deepseek_client()
    prompt = f"""下面是一段成功运行的 Genesis（import genesis as gs）Python 代码。
请列出代码中实际使用到的 API 标识符，要求以 genesis. 开头，不重复，不要编造。
若调用通过变量表达（如 scene.add_entity），请写为 genesis.Scene.add_entity。

任务: {task_id}
代码:
```python
{code[:12000]}
```
只返回 JSON 数组。"""
    resp = client.chat.completions.create(
        model=EXTRACT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    text = (resp.choices[0].message.content or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, list):
            out = [x.strip() for x in data if isinstance(x, str) and x.startswith("genesis.")]
            return sorted(set(out))
    except json.JSONDecodeError:
        pass
    found = set(re.findall(r"genesis\.[a-zA-Z0-9_.]+", code))
    return sorted(found)


def extract_apis_from_code_ast(code: str) -> List[str]:
    """
    用 AST 从代码中提取 API（轻量、无 LLM 调用）。
    目标格式与 expected_apis 对齐：genesis.xxx
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    genesis_aliases = set()   # 例如 {"gs", "genesis"}
    scene_vars = set()        # 例如 {"scene"}
    apis = set()

    def _attr_chain(node: ast.AST) -> Optional[List[str]]:
        parts: List[str] = []
        cur = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
            parts.reverse()
            return parts
        return None

    class Visitor(ast.NodeVisitor):
        def visit_Import(self, node: ast.Import) -> None:
            for n in node.names:
                if n.name == "genesis":
                    genesis_aliases.add(n.asname or "genesis")
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.module == "genesis":
                for n in node.names:
                    if n.name == "*":
                        continue
                    genesis_aliases.add(n.asname or n.name)
            self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            # scene = gs.Scene(...)
            if isinstance(node.value, ast.Call):
                func_parts = _attr_chain(node.value.func)
                if func_parts and len(func_parts) >= 2 and func_parts[0] in genesis_aliases and func_parts[1] == "Scene":
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            scene_vars.add(t.id)
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            parts = _attr_chain(node.func)
            if parts:
                # gs.xxx -> genesis.xxx
                if parts[0] in genesis_aliases and len(parts) > 1:
                    apis.add("genesis." + ".".join(parts[1:]))
                    # 如果是 gs.Scene(...)，补一个 genesis.Scene
                    if parts[1] == "Scene":
                        apis.add("genesis.Scene")

                # scene.add_entity(...) -> genesis.Scene.add_entity
                if parts[0] in scene_vars and len(parts) > 1:
                    apis.add("genesis.Scene." + ".".join(parts[1:]))
            self.generic_visit(node)

    Visitor().visit(tree)
    return sorted(apis)


def _filter_expected_apis(apis: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for api in apis:
        if not isinstance(api, str):
            continue
        s = api.strip()
        if not s:
            continue
        if s in EXCLUDED_APIS:
            continue
        if any(s.startswith(prefix) for prefix in EXCLUDED_API_PREFIXES):
            continue
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _run_one_subprocess(script_path: str, python_exe: str = "") -> Tuple[bool, str]:
    python = python_exe or sys.executable
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTEST_VERSION"] = "1"
    try:
        r = subprocess.run(
            [python, "-u", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=RUN_TIMEOUT,
        )
        return r.returncode == 0, (r.stdout or "")[:4000]
    except subprocess.TimeoutExpired:
        return False, f"(Timeout after {RUN_TIMEOUT}s while running {os.path.basename(script_path)})"
    except Exception as e:
        return False, str(e)


def _sanitize_text(text: str) -> str:
    """Remove ANSI escape codes and replace non-ASCII chars to avoid GBK encoding errors on Windows."""
    import re as _re
    t = _re.sub("\x1b\[[0-9;]*m", "", text)  # strip ANSI escape codes (non-raw string so \x1b matches ESC)
    t = t.encode("ascii", errors="replace").decode("ascii", errors="replace")
    return t


def _brief_error_text(out: str, limit: int = 900) -> str:
    text = _sanitize_text(out or "").strip()
    if not text:
        return "(empty output)"
    tb = "Traceback (most recent call last):"
    idx = text.rfind(tb)
    if idx >= 0:
        seg = text[idx:].strip()
        if len(seg) <= limit:
            return seg
        return "...(truncated head)\n" + seg[-limit:]
    if len(text) <= limit:
        return text
    return "...(truncated head)\n" + text[-limit:]


def _write_script(path: str, task_id: str, query: str, code: str) -> str:
    header = f'"""\nUser Query: {query}\ntask_id: {task_id}\n"""\n\n'
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + code)
    return path


def _load_queries(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("query.json 应为 JSON 数组")
    return data


def _save_queries(path: str, tasks: List[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)


def main() -> None:
    ap = argparse.ArgumentParser(description="根据 query.json 批量生成脚本、验证并补全 expected_apis")
    ap.add_argument("--query-file", default=DEFAULT_QUERY_JSON)
    ap.add_argument("--tasks", default=None)
    ap.add_argument("--max-retries", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-update-query", action="store_true")
    ap.add_argument(
        "--python",
        default="",
        help="Python executable for running generated code (default: sys.executable). "
             "Example: D:/anaconda/envs/env_genesis/python.exe",
    )
    ap.add_argument(
        "--api-extract-mode",
        choices=["llm", "ast", "hybrid"],
        default="ast",
        help="API 提取方式：llm / ast / hybrid（ast+llm）",
    )
    args = ap.parse_args()

    tasks_filter = None
    if args.tasks:
        tasks_filter = {t.strip() for t in args.tasks.split(",") if t.strip()}

    tasks = _load_queries(args.query_file)
    if tasks_filter:
        tasks = [t for t in tasks if t.get("task_id") in tasks_filter]

    if args.dry_run:
        print("dry-run 目标文件：")
        for i, t in enumerate(tasks, start=1):
            tid = str(t.get("task_id"))
            print(f"  {tid} -> {_query_file_path(tid, i - 1)}")
        return

    client = _get_chat_client()
    extracted: Dict[str, List[str]] = {}
    extracted_detail: Dict[str, Dict[str, List[str]]] = {}
    report_lines: List[str] = []

    for i, task in enumerate(tqdm(tasks, desc="query_gen"), start=1):
        task_id = str(task.get("task_id") or "")
        query = task.get("query", "")
        if not task_id or not query:
            report_lines.append(f"{task_id}: SKIP (missing task_id/query)")
            continue

        script_path = _query_file_path(task_id, i - 1)
        ok = False
        last_err = ""
        code_for_api: Optional[str] = None

        print(f"\n[{task_id}] -> {os.path.basename(script_path)}")

        if os.path.isfile(script_path):
            print("  - 已存在脚本，重新执行验证")
            with open(script_path, "r", encoding="utf-8") as f:
                code_for_api = f.read()
            success, out = _run_one_subprocess(script_path, python_exe=args.python)
            if success:
                ok = True
                print("    [OK] 验证通过，直接用于 API 提取")
                report_lines.append(f"{task_id}: OK (existing file)")
            else:
                print(f"    [FAIL] 验证失败，删除后重新生成")
                try:
                    os.remove(script_path)
                except Exception:
                    pass
                code_for_api = None
        else:
            print("  - 不存在脚本，开始生成")

        for attempt in range(1, args.max_retries + 1):
            if ok:
                break
            print(f"  - 生成中 ({attempt}/{args.max_retries})")
            try:
                code = generate_code(client, query, task_id)
            except Exception as e:
                last_err = str(e)
                print(f"    [FAIL] 生成失败: {e}")
                continue

            _write_script(script_path, task_id, query, code)
            print("  - 执行中")
            success, out = _run_one_subprocess(script_path, python_exe=args.python)
            if success:
                ok = True
                code_for_api = code
                print("    [OK] 执行成功")
                report_lines.append(f"{task_id}: OK (gen attempt {attempt})")
                break

            last_err = out[:500]
            print(f"    [FAIL] 执行失败 ({attempt}/{args.max_retries})")
            print(f"      原因: {_brief_error_text(out)}")
            # 保留失败脚本以便后续 build_api_constraint 提取约束

        if ok and code_for_api is not None:
            print("  - 提取 API")
            ast_apis: List[str] = []
            llm_apis: List[str] = []

            if args.api_extract_mode in ("ast", "hybrid"):
                ast_apis = extract_apis_from_code_ast(code_for_api)
            if args.api_extract_mode in ("llm", "hybrid"):
                llm_apis = extract_apis_from_code(code_for_api, task_id)

            if args.api_extract_mode == "ast":
                apis = ast_apis
            elif args.api_extract_mode == "llm":
                apis = llm_apis
            else:
                apis = sorted(set(ast_apis) | set(llm_apis))

            extracted[task_id] = apis
            extracted_detail[task_id] = {
                "ast_apis": sorted(set(ast_apis)),
                "llm_apis": sorted(set(llm_apis)),
            }
            report_lines.append(f"{task_id}: APIs extracted={len(apis)} (mode={args.api_extract_mode})")

        if not ok:
            report_lines.append(f"{task_id}: FAIL after {args.max_retries} tries — {last_err!r}")

    if not args.no_update_query and extracted:
        full = _load_queries(args.query_file)
        for t in full:
            tid = str(t.get("task_id"))
            if tid not in extracted:
                continue
            old = t.get("expected_apis") or []
            if not isinstance(old, list):
                old = []
            merged = list(dict.fromkeys(list(old) + list(extracted[tid])))
            t["expected_apis"] = _filter_expected_apis(merged)
        _save_queries(args.query_file, full)
        print(f"\n[DONE] 已更新 {args.query_file} 中 {len(extracted)} 条 expected_apis")

    report_path = os.path.join(_BENCHMARK_DIR, "results", "query_gen_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("query_gen report\n")
        f.write(f"query_file: {args.query_file}\n")
        f.write(f"model: {GEN_MODEL}\n\n")
        f.write(f"api_extract_mode: {args.api_extract_mode}\n\n")
        f.write("\n".join(report_lines))
        if args.api_extract_mode == "hybrid":
            f.write("\n\n--- hybrid per-task api details ---\n")
            for tid in sorted(extracted_detail.keys()):
                detail = extracted_detail.get(tid, {})
                ast_apis = detail.get("ast_apis", [])
                llm_apis = detail.get("llm_apis", [])
                ast_only = sorted(set(ast_apis) - set(llm_apis))
                llm_only = sorted(set(llm_apis) - set(ast_apis))
                both = sorted(set(ast_apis) & set(llm_apis))
                f.write(f"\n[{tid}]\n")
                f.write(
                    f"  ast_count={len(ast_apis)} llm_count={len(llm_apis)} "
                    f"union_count={len(set(ast_apis) | set(llm_apis))}\n"
                )
                f.write(f"  both({len(both)}): {json.dumps(both, ensure_ascii=False)}\n")
                f.write(f"  ast_only({len(ast_only)}): {json.dumps(ast_only, ensure_ascii=False)}\n")
                f.write(f"  llm_only({len(llm_only)}): {json.dumps(llm_only, ensure_ascii=False)}\n")
    print(f"[REPORT] 明细报告: {report_path}")


if __name__ == "__main__":
    main()

"""
User Query: Control a Franka Panda arm (use gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml")) to move its end-effector to coordinates (0.3, 0.2, 0.4) using joint commands.
task_id: s1_robot_medium_003
"""

import math
import numpy as np
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(1.8, -1.2, 1.2),
        camera_lookat=(0.3, 0.0, 0.4),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.1),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

robot = scene.add_entity(
    morph=gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

target_pos = np.array([0.3, 0.2, 0.4], dtype=float)
home_q = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785], dtype=float)

try:
    robot.set_dofs_position(home_q)
except Exception:
    try:
        robot.set_qpos(home_q)
    except Exception:
        pass

for _ in range(100):
    scene.step()

jacobian_methods = [
    "get_link_jacobian",
    "get_jacobian",
]
fk_methods = [
    "get_link_pos",
    "get_link_position",
    "get_site_pos",
    "get_site_position",
]

ee_name_candidates = [
    "panda_hand",
    "hand",
    "panda_link8",
    "panda_grasptarget",
    "right_hand",
]

ee_ref = None
ee_name = None

for name in ee_name_candidates:
    for fk_name in fk_methods:
        if hasattr(robot, fk_name):
            try:
                getattr(robot, fk_name)(name)
                ee_ref = name
                ee_name = name
                break
            except Exception:
                continue
    if ee_ref is not None:
        break

if ee_ref is None:
    raise RuntimeError("Could not find Panda end-effector link/site name.")

def get_ee_pos():
    for fk_name in fk_methods:
        if hasattr(robot, fk_name):
            try:
                pos = getattr(robot, fk_name)(ee_ref)
                return np.array(pos, dtype=float).reshape(3)
            except Exception:
                continue
    raise RuntimeError("No valid API found to query end-effector position.")

def get_jacobian():
    for jac_name in jacobian_methods:
        if hasattr(robot, jac_name):
            try:
                J = getattr(robot, jac_name)(ee_ref)
                J = np.array(J, dtype=float)
                if J.ndim == 2 and J.shape[0] >= 3:
                    return J[:3, :7]
            except Exception:
                continue
    raise RuntimeError("No valid API found to query end-effector Jacobian.")

def set_arm_q(q):
    q = np.array(q, dtype=float).reshape(7)
    if hasattr(robot, "control_dofs_position"):
        try:
            robot.control_dofs_position(q, dofs_idx=list(range(7)))
            return
        except Exception:
            pass
    if hasattr(robot, "set_dofs_position"):
        try:
            robot.set_dofs_position(q, dofs_idx=list(range(7)))
            return
        except Exception:
            try:
                robot.set_dofs_position(q)
                return
            except Exception:
                pass
    if hasattr(robot, "set_qpos"):
        try:
            robot.set_qpos(q)
            return
        except Exception:
            pass
    raise RuntimeError("No valid API found to send joint position commands.")

q = home_q.copy()
max_iters = 300
alpha = 0.5
damping = 1e-3

for i in range(max_iters):
    ee_pos = get_ee_pos()
    err = target_pos - ee_pos
    err_norm = np.linalg.norm(err)

    if err_norm < 1e-3:
        print(f"Target reached at iter {i}, ee_pos={ee_pos}")
        break

    J = get_jacobian()
    JT = J.T
    dq = JT @ np.linalg.solve(J @ JT + damping * np.eye(3), err)

    step_limit = 0.08
    dq_norm = np.linalg.norm(dq)
    if dq_norm > step_limit:
        dq = dq * (step_limit / dq_norm)

    q = q + alpha * dq
    set_arm_q(q)

    for _ in range(5):
        scene.step()

final_pos = get_ee_pos()
final_err = target_pos - final_pos

print("Target position:", target_pos.tolist())
print("Final end-effector position:", final_pos.tolist())
print("Final error:", final_err.tolist(), "norm =", float(np.linalg.norm(final_err)))

for _ in range(200):
    scene.step()
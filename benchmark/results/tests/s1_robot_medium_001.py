"""
User Query: Load a Franka Panda robot arm (use gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml")) and command it to reach a target position in front of it using smooth joint motion.
task_id: s1_robot_medium_001
"""

import math
import numpy as np
import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.2, -2.0, 1.6),
        camera_lookat=(0.4, 0.0, 0.6),
    ),
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.1),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

target_pos = np.array([0.45, 0.0, 0.35], dtype=float)

all_joints = robot.get_joint_names()
arm_joint_names = [name for name in all_joints if "joint" in name and "finger" not in name][:7]
arm_dofs = [robot.get_joint(name).dof_idx_local for name in arm_joint_names]

ee_link = None
for link_name in ["hand", "panda_hand", "ee", "panda_link8"]:
    try:
        ee_link = robot.get_link(link_name)
        break
    except Exception:
        pass
if ee_link is None:
    raise RuntimeError("Could not find Panda end-effector link.")

q_start = np.array([0.0, -0.5, 0.0, -2.0, 0.0, 1.6, 0.8], dtype=float)
robot.set_dofs_position(q_start, dofs_idx_local=arm_dofs)

for _ in range(50):
    scene.step()

q_current = q_start.copy()
q_goal = q_current.copy()

step_eps = 1e-3
alpha = 0.35
max_ik_iters = 120

for _ in range(max_ik_iters):
    robot.set_dofs_position(q_goal, dofs_idx_local=arm_dofs)
    ee_pos = np.array(ee_link.get_pos(), dtype=float)
    err = target_pos - ee_pos
    if np.linalg.norm(err) < 1e-3:
        break

    J = np.zeros((3, 7), dtype=float)
    for i in range(7):
        q_perturb = q_goal.copy()
        q_perturb[i] += step_eps
        robot.set_dofs_position(q_perturb, dofs_idx_local=arm_dofs)
        p_perturb = np.array(ee_link.get_pos(), dtype=float)
        J[:, i] = (p_perturb - ee_pos) / step_eps

    robot.set_dofs_position(q_goal, dofs_idx_local=arm_dofs)

    dq = alpha * np.linalg.pinv(J) @ err
    q_goal += dq

q_goal = np.clip(
    q_goal,
    np.array([-2.8, -1.8, -2.8, -3.0, -2.8, -0.5, -2.8]),
    np.array([ 2.8,  1.8,  2.8, -0.05, 2.8,  3.5,  2.8]),
)

move_steps = 300
hold_steps = 200

for t in range(move_steps):
    s = (t + 1) / move_steps
    s_smooth = 3 * s**2 - 2 * s**3
    q_cmd = (1.0 - s_smooth) * q_start + s_smooth * q_goal
    robot.set_dofs_position(q_cmd, dofs_idx_local=arm_dofs)
    scene.step()

for _ in range(hold_steps):
    robot.set_dofs_position(q_goal, dofs_idx_local=arm_dofs)
    scene.step()
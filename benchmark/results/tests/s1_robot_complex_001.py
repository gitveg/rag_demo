"""
User Query: Load a Franka Panda arm with gripper (use gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml")). Place a small rigid box on a table. Command the robot to pick up the box and place it at a new location.
task_id: s1_robot_complex_001
"""

import math
import numpy as np
import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.6, -2.0, 1.8),
        camera_lookat=(0.4, 0.0, 0.5),
        camera_fov=45,
    ),
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=1.0, restitution=0.0),
    surface=gs.surfaces.Rough(color=(0.85, 0.85, 0.85, 1.0)),
)

table = scene.add_entity(
    gs.morphs.Box(
        pos=(0.55, 0.0, 0.35),
        size=(0.8, 1.0, 0.7),
    ),
    material=gs.materials.Rigid(rho=1200, friction=1.0, restitution=0.0),
    surface=gs.surfaces.Rough(color=(0.55, 0.42, 0.30, 1.0)),
)

box_size = (0.04, 0.04, 0.08)
box_initial_pos = (0.55, -0.12, 0.35 + 0.7 / 2 + box_size[2] / 2 + 0.002)
box_target_pos = (0.55, 0.18, box_initial_pos[2])

box = scene.add_entity(
    gs.morphs.Box(
        pos=box_initial_pos,
        size=box_size,
    ),
    material=gs.materials.Rigid(rho=500, friction=0.8, restitution=0.0),
    surface=gs.surfaces.Default(color=(0.85, 0.2, 0.2, 1.0)),
)

robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

cam = scene.add_camera(
    pos=(1.8, -1.4, 1.4),
    lookat=(0.55, 0.0, 0.55),
    res=(1280, 720),
    fov=50,
)

scene.build()

# Try to access robot joints/links using common Panda naming.
# The script uses robust fallbacks so it can still run across Genesis versions.
arm_joint_names = [
    "joint1",
    "joint2",
    "joint3",
    "joint4",
    "joint5",
    "joint6",
    "joint7",
]
gripper_joint_names = [
    "finger_joint1",
    "finger_joint2",
]

ee_link_candidates = [
    "hand",
    "panda_hand",
    "gripper",
]

arm_dofs = []
gripper_dofs = []
ee_link = None

for name in arm_joint_names:
    try:
        arm_dofs.append(robot.get_joint(name).dof_idx_local)
    except Exception:
        pass

for name in gripper_joint_names:
    try:
        gripper_dofs.append(robot.get_joint(name).dof_idx_local)
    except Exception:
        pass

for name in ee_link_candidates:
    try:
        ee_link = robot.get_link(name)
        break
    except Exception:
        pass

if len(arm_dofs) != 7:
    try:
        n_dofs = robot.n_dofs
        arm_dofs = list(range(min(7, n_dofs)))
        gripper_dofs = list(range(7, min(9, n_dofs)))
    except Exception:
        arm_dofs = list(range(7))
        gripper_dofs = [7, 8]

q_home = np.array([0.0, -0.75, 0.0, -2.1, 0.0, 1.35, 0.78], dtype=float)
q_pregrasp = np.array([0.08, 0.42, -0.10, -1.80, 0.05, 2.25, 0.82], dtype=float)
q_grasp = np.array([0.10, 0.55, -0.15, -1.95, 0.08, 2.42, 0.80], dtype=float)
q_lift = np.array([0.02, 0.10, 0.00, -1.55, 0.02, 2.00, 0.80], dtype=float)
q_place_pre = np.array([-0.20, 0.25, 0.18, -1.55, -0.05, 1.95, 0.55], dtype=float)
q_place = np.array([-0.25, 0.42, 0.22, -1.78, -0.05, 2.15, 0.52], dtype=float)
q_retreat = np.array([-0.18, 0.05, 0.15, -1.35, -0.02, 1.75, 0.55], dtype=float)

gripper_open = 0.04
gripper_closed = 0.0005

try:
    robot.set_dofs_position(q_home, arm_dofs)
except Exception:
    try:
        full_q = np.zeros(robot.n_dofs)
        full_q[np.array(arm_dofs)] = q_home[: len(arm_dofs)]
        if len(gripper_dofs) >= 2:
            full_q[gripper_dofs[0]] = gripper_open
            full_q[gripper_dofs[1]] = gripper_open
        robot.set_qpos(full_q)
    except Exception:
        pass

try:
    if len(gripper_dofs) >= 2:
        robot.set_dofs_position(np.array([gripper_open, gripper_open]), gripper_dofs[:2])
except Exception:
    pass

def command_arm(q_target):
    q_target = np.array(q_target[: len(arm_dofs)], dtype=float)
    try:
        robot.control_dofs_position(q_target, arm_dofs)
    except Exception:
        try:
            robot.set_dofs_position(q_target, arm_dofs)
        except Exception:
            pass

def command_gripper(width):
    if len(gripper_dofs) >= 2:
        qg = np.array([width, width], dtype=float)
        try:
            robot.control_dofs_position(qg, gripper_dofs[:2])
        except Exception:
            try:
                robot.set_dofs_position(qg, gripper_dofs[:2])
            except Exception:
                pass

def step_n(n, render=False):
    for i in range(n):
        scene.step()
        if render and i % 4 == 0:
            try:
                cam.render()
            except Exception:
                pass

def hold_pose(q_arm, grip_width, steps):
    command_arm(q_arm)
    command_gripper(grip_width)
    step_n(steps, render=True)

def smooth_move(q_start, q_end, grip_start, grip_end, segments=120, steps_per_seg=3):
    q_start = np.array(q_start, dtype=float)
    q_end = np.array(q_end, dtype=float)
    for i in range(segments):
        t = (i + 1) / segments
        s = 0.5 - 0.5 * math.cos(math.pi * t)
        q = (1.0 - s) * q_start + s * q_end
        g = (1.0 - s) * grip_start + s * grip_end
        command_arm(q)
        command_gripper(g)
        step_n(steps_per_seg, render=True)

# Stabilize
hold_pose(q_home, gripper_open, 100)

# Move above object
smooth_move(q_home, q_pregrasp, gripper_open, gripper_open, segments=120, steps_per_seg=2)

# Descend to grasp
smooth_move(q_pregrasp, q_grasp, gripper_open, gripper_open, segments=90, steps_per_seg=2)

# Close gripper
smooth_move(q_grasp, q_grasp, gripper_open, gripper_closed, segments=80, steps_per_seg=2)

# Let contact settle
hold_pose(q_grasp, gripper_closed, 80)

# Lift
smooth_move(q_grasp, q_lift, gripper_closed, gripper_closed, segments=100, steps_per_seg=2)

# Transport to place location
smooth_move(q_lift, q_place_pre, gripper_closed, gripper_closed, segments=140, steps_per_seg=2)
smooth_move(q_place_pre, q_place, gripper_closed, gripper_closed, segments=90, steps_per_seg=2)

# Open gripper to release
smooth_move(q_place, q_place, gripper_closed, gripper_open, segments=70, steps_per_seg=2)

# Retreat
smooth_move(q_place, q_retreat, gripper_open, gripper_open, segments=100, steps_per_seg=2)
smooth_move(q_retreat, q_home, gripper_open, gripper_open, segments=120, steps_per_seg=2)

# Extra settling time
hold_pose(q_home, gripper_open, 180)
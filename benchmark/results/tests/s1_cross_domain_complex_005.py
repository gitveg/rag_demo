"""
User Query: A robotic arm attempts to pick up a soft, deformable elastic cube and move it to a different location on a bumpy terrain.
task_id: s1_cross_domain_complex_005
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
        substeps=10,
        gravity=(0.0, 0.0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.5, -3.5, 2.6),
        camera_lookat=(0.8, 0.0, 0.5),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

terrain = scene.add_entity(
    morph=gs.morphs.Terrain(
        pos=(0.0, 0.0, 0.0),
        n_subterrains=(3, 3),
        subterrain_size=(12, 12),
        horizontal_scale=0.25,
        vertical_scale=0.005,
        subterrain_types=[
            ["flat_terrain", "wave_terrain", "flat_terrain"],
            ["sloped_terrain", "fractal_terrain", "stairs_terrain"],
            ["flat_terrain", "random_uniform_terrain", "flat_terrain"],
        ],
    ),
    material=gs.materials.Rigid(rho=2500, friction=1.0, restitution=0.05),
    surface=gs.surfaces.Rough(color=(0.45, 0.42, 0.38, 1.0)),
)

robot = scene.add_entity(
    morph=gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

soft_cube = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.55, 0.0, 0.14),
        size=(0.10, 0.10, 0.10),
    ),
    material=gs.materials.FEM.Elastic(
        density=1000,
        youngs_modulus=1e5,
        poissons_ratio=0.3,
    ),
    surface=gs.surfaces.Default(color=(0.85, 0.25, 0.25, 1.0)),
)

target_marker = scene.add_entity(
    morph=gs.morphs.Cylinder(
        pos=(1.05, 0.45, 0.03),
        radius=0.12,
        height=0.06,
    ),
    material=gs.materials.Rigid(rho=500, friction=0.9, restitution=0.0),
    surface=gs.surfaces.Emission(color=(0.2, 0.8, 0.2, 1.0)),
)

scene.add_camera(
    pos=(2.8, -2.4, 1.8),
    lookat=(0.8, 0.1, 0.35),
    res=(1280, 720),
    fov=50,
)

scene.build()

try:
    robot.set_qpos([0.0, -0.6, 0.0, -2.2, 0.0, 1.6, 0.8, 0.04, 0.04])
except Exception:
    pass

ee_link_candidates = [
    "panda_hand",
    "hand",
    "ee",
    "panda_leftfinger",
]
finger_joint_candidates = [
    ("panda_finger_joint1", "panda_finger_joint2"),
    ("finger_joint1", "finger_joint2"),
]

ee_link = None
for name in ee_link_candidates:
    try:
        ee_link = robot.get_link(name)
        break
    except Exception:
        continue

finger_joints = None
for j1, j2 in finger_joint_candidates:
    try:
        finger_joints = (robot.get_joint(j1), robot.get_joint(j2))
        break
    except Exception:
        continue

arm_joint_names = [
    "panda_joint1",
    "panda_joint2",
    "panda_joint3",
    "panda_joint4",
    "panda_joint5",
    "panda_joint6",
    "panda_joint7",
]
arm_joints = []
for name in arm_joint_names:
    try:
        arm_joints.append(robot.get_joint(name))
    except Exception:
        pass

home_q = [0.0, -0.6, 0.0, -2.2, 0.0, 1.6, 0.8]
pregrasp_q = [0.15, -0.35, 0.05, -1.95, 0.0, 1.75, 0.65]
grasp_q = [0.20, -0.20, 0.10, -1.80, 0.0, 1.85, 0.55]
lift_q = [0.05, -0.55, 0.0, -2.05, 0.1, 1.65, 0.75]
transport_q = [0.55, -0.30, 0.10, -1.70, 0.25, 1.55, 0.30]
place_q = [0.70, -0.12, 0.18, -1.55, 0.35, 1.45, 0.10]
retreat_q = [0.45, -0.45, 0.05, -1.95, 0.15, 1.60, 0.45]

def set_arm_targets(q):
    if len(arm_joints) == 7:
        for joint, val in zip(arm_joints, q):
            try:
                joint.set_target_position(val)
            except Exception:
                try:
                    joint.set_qpos(val)
                except Exception:
                    pass

def set_gripper(opening):
    if finger_joints is not None:
        for joint in finger_joints:
            try:
                joint.set_target_position(opening)
            except Exception:
                try:
                    joint.set_qpos(opening)
                except Exception:
                    pass

def hold_pose(q, opening, steps):
    for _ in range(steps):
        set_arm_targets(q)
        set_gripper(opening)
        scene.step()

schedule = [
    (home_q, 0.04, 80),
    (pregrasp_q, 0.04, 140),
    (grasp_q, 0.04, 120),
    (grasp_q, 0.015, 120),
    (lift_q, 0.012, 140),
    (transport_q, 0.012, 180),
    (place_q, 0.012, 140),
    (place_q, 0.04, 100),
    (retreat_q, 0.04, 140),
]

for q, g, n in schedule:
    hold_pose(q, g, n)

for _ in range(200):
    set_arm_targets(retreat_q)
    set_gripper(0.04)
    scene.step()
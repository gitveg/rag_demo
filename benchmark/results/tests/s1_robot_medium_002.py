"""
User Query: Create a robotic arm that picks up a small cube from one location and places it onto a nearby platform.
task_id: s1_robot_medium_002
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.5, -2.0, 1.8),
        camera_lookat=(0.5, 0.0, 0.4),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

ground = scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=2000, friction=0.8, restitution=0.1),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

table = scene.add_entity(
    morph=gs.morphs.Box(pos=(0.5, 0.0, 0.35), size=(1.0, 1.2, 0.1)),
    material=gs.materials.Rigid(rho=800, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Default(color=(0.5, 0.35, 0.2, 1.0)),
)

platform = scene.add_entity(
    morph=gs.morphs.Box(pos=(0.72, 0.22, 0.46), size=(0.18, 0.18, 0.12)),
    material=gs.materials.Rigid(rho=900, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

cube = scene.add_entity(
    morph=gs.morphs.Box(pos=(0.45, -0.22, 0.43), size=(0.05, 0.05, 0.05)),
    material=gs.materials.Rigid(rho=500, friction=0.8, restitution=0.05),
    surface=gs.surfaces.Default(color=(0.9, 0.2, 0.2, 1.0)),
)

robot = scene.add_entity(
    morph=gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

cam = scene.add_camera(
    pos=(2.0, -1.6, 1.4),
    lookat=(0.55, 0.0, 0.45),
    res=(960, 640),
    fov=50,
)

scene.build()

if hasattr(robot, "set_base_pos"):
    robot.set_base_pos((0.0, 0.0, 0.0))

if hasattr(robot, "set_qpos"):
    try:
        q_init = [0.0, -0.6, 0.0, -2.0, 0.0, 1.5, 0.8, 0.04, 0.04]
        robot.set_qpos(q_init)
    except Exception:
        pass

for _ in range(100):
    scene.step()

home_q = [0.0, -0.6, 0.0, -2.0, 0.0, 1.5, 0.8]
pre_grasp_q = [0.15, 0.25, 0.0, -1.95, 0.0, 2.25, 0.65]
grasp_q = [0.18, 0.38, 0.03, -2.15, 0.02, 2.45, 0.62]
lift_q = [0.12, 0.10, 0.02, -1.80, 0.02, 2.15, 0.70]
pre_place_q = [-0.20, 0.10, 0.10, -1.75, -0.05, 2.00, 0.65]
place_q = [-0.24, 0.28, 0.10, -1.95, -0.08, 2.15, 0.62]
retreat_q = [-0.18, -0.02, 0.08, -1.65, -0.05, 1.90, 0.72]

def command_arm(arm_q, finger_width, steps=120):
    q = list(arm_q) + [finger_width, finger_width]
    if hasattr(robot, "control_dofs_position"):
        try:
            robot.control_dofs_position(q)
        except Exception:
            try:
                robot.set_qpos(q)
            except Exception:
                pass
    else:
        try:
            robot.set_qpos(q)
        except Exception:
            pass

    for _ in range(steps):
        scene.step()

command_arm(home_q, 0.04, steps=120)
command_arm(pre_grasp_q, 0.04, steps=180)
command_arm(grasp_q, 0.04, steps=140)
command_arm(grasp_q, 0.0, steps=160)
command_arm(lift_q, 0.0, steps=180)
command_arm(pre_place_q, 0.0, steps=180)
command_arm(place_q, 0.0, steps=150)
command_arm(place_q, 0.04, steps=180)
command_arm(retreat_q, 0.04, steps=180)
command_arm(home_q, 0.04, steps=180)

for _ in range(300):
    scene.step()
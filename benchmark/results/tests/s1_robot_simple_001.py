"""
User Query: Load a Franka Panda robot arm from MJCF file (use gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml")) and move its first joint to a 45-degree angle.
task_id: s1_robot_simple_001
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.5, -2.0, 1.8),
        camera_lookat=(0.0, 0.0, 0.6),
    ),
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.1),
    surface=gs.surfaces.Default(color=(0.9, 0.9, 0.9, 1.0)),
)

robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

scene.step()

try:
    qpos = robot.get_qpos()
    if hasattr(qpos, "__len__") and len(qpos) > 0:
        qpos[0] = math.pi / 4.0
        robot.set_qpos(qpos)
except Exception:
    try:
        robot.set_qpos([math.pi / 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    except Exception:
        pass

for _ in range(500):
    scene.step()
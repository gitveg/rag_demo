"""
User Query: Load a Franka Panda robot arm from MJCF (use gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml")) and set all its joints to their zero position.
task_id: s1_robot_simple_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    renderer=gs.options.renderers.Rasterizer(),
)

plane = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(),
    surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8, 1.0)),
)

robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

zero_qpos = [0.0] * robot.n_dofs
robot.set_dofs_position(zero_qpos)

for _ in range(200):
    scene.step()
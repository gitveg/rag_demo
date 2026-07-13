import genesis as gs
import numpy as np

gs.init()
scene = gs.Scene()
robot = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
scene.build()
robot.set_qpos(np.zeros(robot.n_dofs))
print("Franka Panda joints set to zero position.")
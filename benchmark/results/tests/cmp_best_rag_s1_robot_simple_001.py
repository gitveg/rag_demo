import genesis as gs
import numpy as np

########################## init ##########################
gs.init()

########################## create a scene ##########################
scene = gs.Scene()

########################## entities ##########################
plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

########################## control ##########################
# first joint to 45 degrees, others hold default positions
target_q = np.array([0.785398, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.04, 0.04])

for _ in range(500):
    franka.control_dofs_position(target_q)
    scene.step()
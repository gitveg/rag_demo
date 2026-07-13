import genesis as gs
import numpy as np

gs.init(backend=gs.cpu)

scene = gs.Scene()

franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

zero_qpos = np.zeros(franka.n_dofs)
franka.set_qpos(zero_qpos)

for i in range(100):
    scene.step()
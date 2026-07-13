import genesis as gs
import numpy as np

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))

scene.build()

franka.set_dofs_position(np.zeros(franka.n_dofs))

for _ in range(100):
    scene.step()
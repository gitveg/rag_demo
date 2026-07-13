import genesis as gs
import math

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(
    gs.morphs.Plane(),
)
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

# Set first joint to 45 degrees (π/4 radians)
qpos = franka.get_qpos()
qpos[0] = math.pi / 4
franka.set_qpos(qpos)

for i in range(1000):
    scene.step()
import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(
    gs.morphs.Plane(),
)
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)
table = scene.add_entity(
    gs.morphs.Box(pos=(0.5, 0.0, 0.4), size=(1.0, 0.5, 0.05)),
    material=gs.materials.Rigid(),
)
box = scene.add_entity(
    gs.morphs.Box(pos=(0.5, 0.1, 0.45), size=(0.05, 0.05, 0.05)),
    material=gs.materials.Rigid(),
)

scene.build()

# TODO: Implement pick-and-place control using robot's joint/motor interface
for i in range(1000):
    scene.step()
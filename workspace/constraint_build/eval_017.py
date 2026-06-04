import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(
    gs.morphs.Plane(),
)

franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

box = scene.add_entity(
    gs.morphs.Box(size=(0.1, 0.1, 0.1), pos=(0.5, 0, 0.25)),
)

scene.build()

for i in range(100):
    scene.step()
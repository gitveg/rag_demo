import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(
    gs.morphs.Plane(),
)
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)
red_box = scene.add_entity(
    gs.morphs.Box(pos=(0.6, 0.0, 0.05), size=(0.1, 0.1, 0.1)),
    surface=gs.surfaces.Default(color=(1.0, 0.0, 0.0, 1.0)),
)

scene.build()
for i in range(1000):
    scene.step()
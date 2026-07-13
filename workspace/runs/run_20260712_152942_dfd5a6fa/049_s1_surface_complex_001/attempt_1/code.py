import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(
    gs.morphs.Plane(),
)

franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
    surface=gs.surfaces.Metal(
        color=(0.9, 0.9, 0.9),
        roughness=0.1,
    ),
)

box = scene.add_entity(
    gs.morphs.Box(
        pos=(0.5, 0.0, 0.05),
        size=(0.2, 0.2, 0.1),
    ),
    surface=gs.surfaces.Glass(
        color=(1.0, 0.0, 0.0, 0.5),
        roughness=0.5,
    ),
)

scene.build()
for i in range(1000):
    scene.step()
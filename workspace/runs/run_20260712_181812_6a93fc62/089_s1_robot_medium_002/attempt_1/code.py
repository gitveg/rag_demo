import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(
    gs.morphs.Plane(),
)

franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

# Small cube to be picked up
cube = scene.add_entity(
    gs.morphs.Box(
        pos=(0.4, 0.0, 0.1),
        size=(0.04, 0.04, 0.04),
        fixed=False,
    ),
)

# Platform to place cube onto
platform = scene.add_entity(
    gs.morphs.Box(
        pos=(0.6, 0.0, 0.025),
        size=(0.3, 0.3, 0.05),
        fixed=True,
    ),
)

scene.build()
for i in range(1000):
    scene.step()
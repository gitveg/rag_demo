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
    gs.morphs.Box(
        pos=(0.5, 0.0, 0.025),  # placed on the ground in front of the robot
        size=(0.05, 0.05, 0.05),
    ),
)

scene.build()
for i in range(1000):
    scene.step()
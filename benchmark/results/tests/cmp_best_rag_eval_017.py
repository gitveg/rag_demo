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
        pos=(0.5, 0.0, 0.025),  # in front of the robot, on the ground
        size=(0.05, 0.05, 0.05),
    ),
    material=gs.materials.Rigid(),
    surface=gs.surfaces.Default(color=(1, 0, 0, 1)),  # red color
)

scene.build()
for i in range(1000):
    scene.step()
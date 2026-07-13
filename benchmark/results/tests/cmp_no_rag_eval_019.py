import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
        gravity=(0, 0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(5, -5, 5),
        camera_lookat=(0, 0, 1),
    ),
)

# ground
plane = scene.add_entity(gs.morphs.Plane())

# ramp (static tilted box)
ramp = scene.add_entity(
    gs.morphs.Box(
        pos=(2, 0, 0.5),
        size=(4, 0.2, 1),
        fixed=True,
        collision=True,
        euler=(0, 20, 0),
    ),
    material=gs.materials.Rigid(),
)

# rolling sphere
sphere = scene.add_entity(
    gs.morphs.Sphere(
        pos=(1.8, 0, 1.2),
        radius=0.3,
        collision=True,
    ),
    material=gs.materials.Rigid(),
)

# stack of three boxes
box_size = (0.6, 0.6, 0.6)
for i in range(3):
    box = scene.add_entity(
        gs.morphs.Box(
            pos=(3.5, 0, 0.3 + i * 0.6),
            size=box_size,
            collision=True,
        ),
        material=gs.materials.Rigid(),
    )

scene.build()

# run simulation
for _ in range(2000):
    scene.step()
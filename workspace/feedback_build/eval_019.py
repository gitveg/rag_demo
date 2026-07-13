import genesis as gs

gs.init(precision="32", logging_level="info")

scene = gs.Scene(
    rigid_options=gs.options.RigidOptions(gravity=(0, 0, -9.81)),
    viewer_options=gs.options.ViewerOptions(
        res=(1280, 720),
        camera_pos=(2.0, 2.0, 1.5),
        camera_lookat=(0.0, 0.0, 0.3),
        camera_fov=40,
    ),
)

scene.add_entity(gs.morphs.Plane())

scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 0.5),
        size=(1.0, 0.5, 0.1),
        euler=(0.0, 0.35, 0.0),
        fixed=True,
    ),
    material=gs.materials.Rigid(),
)

scene.add_entity(
    gs.morphs.Sphere(
        pos=(-0.45, 0.0, 0.75),
        radius=0.05,
    ),
    material=gs.materials.Rigid(),
)

box_size = 0.1
for i, z in enumerate((0.05, 0.15, 0.25)):
    scene.add_entity(
        gs.morphs.Box(
            pos=(0.7, 0.0, z),
            size=(box_size, box_size, box_size),
        ),
        material=gs.materials.Rigid(),
    )

scene.build()

for _ in range(500):
    scene.step()
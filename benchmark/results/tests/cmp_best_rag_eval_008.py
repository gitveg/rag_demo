import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.5, 0.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.5),
    ),
    show_viewer=True,
)

# large static box
scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.0),
        size=(1.0, 1.0, 0.2),
        fixed=True,
    ),
    material=gs.materials.Rigid(),
)

# small falling sphere
scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(0.0, 0.0, 0.5),
        radius=0.1,
    ),
    material=gs.materials.Rigid(),
)

scene.build()

for _ in range(1000):
    scene.step()
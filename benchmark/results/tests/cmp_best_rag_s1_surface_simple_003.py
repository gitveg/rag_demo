import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, 3.0, 3.0),
        camera_lookat=(0.0, 0.0, 0.0),
    ),
)

sphere = scene.add_entity(
    morph=gs.options.morphs.Sphere(
        pos=(0.0, 0.0, 0.0),
        radius=0.5,
    ),
    surface=gs.options.surfaces.Rough(
        color=(1.0, 0.0, 0.0),
    ),
)

scene.build()

for _ in range(200):
    scene.step()
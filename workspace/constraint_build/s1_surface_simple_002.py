import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.5, 0.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.0),
    ),
    show_viewer=True,
)

plane = scene.add_entity(
    morph=gs.options.morphs.Mesh(
        file=gs.utils.assets.get_tank_mesh(),
        scale=2.0,
    ),
)

sphere = scene.add_entity(
    morph=gs.options.morphs.Sphere(
        pos=(0.0, 0.5, 0.0),
        radius=0.5,
    ),
)

scene.build()

for i in range(1000):
    scene.step()
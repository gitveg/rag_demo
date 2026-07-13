import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3, 2, 3),
        camera_lookat=(0, 0.5, 0),
    ),
)

floor = scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(),
)

sand_column = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0, 0, 0.3),
        size=(0.2, 0.2, 0.5),
    ),
    material=gs.materials.Granular(),
    surface=gs.surfaces.Default(),
)

scene.build()

for _ in range(500):
    scene.step()
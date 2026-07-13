import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(8, -5, 5),
        camera_lookat=(0, 0, 0),
        camera_fov=40,
    ),
)

terrain = scene.add_entity(
    gs.morphs.Terrain(
        subterrain_types="sloped_terrain",
    ),
)

sphere = scene.add_entity(
    gs.morphs.Sphere(
        pos=(2, 0, 2),
        radius=0.2,
    ),
    material=gs.materials.Rigid(),
)

scene.build()

for _ in range(2000):
    scene.step()
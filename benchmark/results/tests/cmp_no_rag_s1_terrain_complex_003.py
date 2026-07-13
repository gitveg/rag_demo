import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(5, -5, 5),
        camera_lookat=(0, 0, 0),
        camera_fov=40,
    ),
    sim_options=gs.options.SimOptions(
        dt=0.01,
        gravity=(0, 0, -9.81),
    ),
)

terrain = scene.add_entity(
    gs.morphs.Mesh(file="meshes/terrain_45.obj"),
    material=gs.materials.Rigid(),
    fixed=True,
)

ball = scene.add_entity(
    gs.morphs.Sphere(radius=0.5, pos=(0, 0, 3.0)),
    material=gs.materials.Rigid(),
)

scene.build()

for i in range(2000):
    scene.step()
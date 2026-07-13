import genesis as gs

gs.init(backend=gs.gpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(0, 0, 10),
        camera_lookat=(0, 0, 0),
    ),
    show_viewer=True,
)

plane = scene.add_entity(
    gs.morphs.Plane(),
)

sphere = scene.add_entity(
    gs.morphs.Sphere(
        pos=(0, 0, 5),
        radius=0.5,
    ),
    material=gs.materials.Rigid(),
)

scene.build()

for _ in range(500):
    scene.step()
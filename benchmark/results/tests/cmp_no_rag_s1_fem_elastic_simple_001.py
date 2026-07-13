import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    show_viewer=True,
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3, 2, 3),
        camera_lookat=(0.0, 0.5, 0.0),
    ),
)

plane = scene.add_entity(
    gs.morphs.Plane(),
)

ball = scene.add_entity(
    gs.morphs.Sphere(
        pos=(0.0, 2.0, 0.0),
        radius=0.3,
    ),
    material=gs.materials.FEM.Elastic(
        E=1e5,
        nu=0.3,
    ),
)

scene.build()

for _ in range(1000):
    scene.step()
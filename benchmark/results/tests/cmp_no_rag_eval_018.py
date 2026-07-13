import genesis as gs

gs.init(backend=gs.gpu)

scene = gs.Scene(
    sim_options=gs.options.Sim(
        dt=0.005,
        gravity=(0, 0, -9.81),
    ),
    viewer_options=gs.options.Viewer(
        show_viewer=True,
        camera_pos=(3, -3, 2),
        camera_lookat=(0, 0, 0.5),
    ),
)

plane = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(),
)

bathtub = scene.add_entity(
    gs.morphs.Mesh(
        file="bathtub.obj",
        scale=(1.0, 1.0, 1.0),
        pos=(0, 0, 0.05),
    ),
    material=gs.materials.Rigid(),
    is_fixed=True,
)

liquid = scene.add_entity(
    gs.morphs.Box(
        pos=(0, 0, 1.2),
        size=(0.4, 0.6, 0.4),
    ),
    material=gs.materials.MPM.Liquid(
        density=1000,
        mu=0.01,
        lambda=500.0,
    ),
    surface=gs.surfaces.Default(),
)

scene.build()

for _ in range(1000):
    scene.step()
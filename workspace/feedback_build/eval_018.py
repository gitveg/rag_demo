import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    mpm_options=gs.options.MPMOptions(
        lower_bound=(-1.0, -1.0, -0.1),
        upper_bound=(1.0, 1.0, 1.5),
    ),
    vis_options=gs.options.VisOptions(
        visualize_mpm_boundary=True,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_fov=30,
        res=(960, 640),
    ),
    show_viewer=True,
)

# Rigid ground plane
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

# Bathtub as a static rigid container (mesh)
bathtub = scene.add_entity(
    material=gs.materials.Rigid(),
    morph=gs.morphs.Mesh(
        file="bathtub.obj",
        pos=(0.0, 0.0, 0.0),
        euler=(0.0, 0.0, 0.0),
        scale=1.0,
    ),
    surface=gs.surfaces.Default(vis_mode="visual"),
)

# Liquid volume to pour from above the bathtub
liquid = scene.add_entity(
    material=gs.materials.MPM.Liquid(),
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.8),
        size=(0.3, 0.3, 0.3),
    ),
    surface=gs.surfaces.Default(
        color=(0.3, 0.3, 1.0),
        vis_mode="particle",
    ),
)

scene.build()

# Fix bathtub so it remains static
bathtub.set_fixed(True)

# Simulate for a few seconds
for _ in range(1000):
    scene.step()
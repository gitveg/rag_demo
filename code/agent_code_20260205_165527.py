import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    mpm_options=gs.options.MPMOptions(
        lower_bound=(-0.5, -1.0, 0.0),
        upper_bound=(0.5, 1.0, 1),
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

plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

colloid_ball = scene.add_entity(
    material=gs.materials.MPM.Elastic(),
    morph=gs.morphs.Box(
        pos=(0.0, 0.5, 0.25),
        size=(0.2, 0.2, 0.2),
    ),
    surface=gs.surfaces.Default(
        color=(0.0, 1.0, 0.4),
        vis_mode="visual",
    ),
)

liquid_ball = scene.add_entity(
    material=gs.materials.MPM.Elastic(),
    morph=gs.morphs.Box(
        pos=(0.0, -0.5, 0.25),
        size=(0.2, 0.2, 0.2),
    ),
    surface=gs.surfaces.Default(
        color=(0.4, 0.6, 1.0),
        vis_mode="visual",
    ),
)

scene.build()

for _ in range(500):
    scene.step()
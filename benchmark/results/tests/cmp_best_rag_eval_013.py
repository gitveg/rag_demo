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

sphere = scene.add_entity(
    morph=gs.options.morphs.Sphere(
        pos=(0.0, 0.0, 0.6),
        radius=0.1,
    ),
    material=gs.materials.MPM.Elastic(),
)

scene.build()

for _ in range(500):
    scene.step()
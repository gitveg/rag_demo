import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    mpm_options=gs.options.MPMOptions(
        lower_bound=(-0.5, -0.5, 0.0),
        upper_bound=(0.5, 0.5, 1.2),
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

# ground plane
scene.add_entity(gs.morphs.Plane())

# first sand block (lower)
scene.add_entity(
    morph=gs.morphs.Box(pos=(0.0, 0.0, 0.4), size=(0.15, 0.15, 0.15)),
    material=gs.materials.MPM.Sand(),
)

# second sand block (higher)
scene.add_entity(
    morph=gs.morphs.Box(pos=(0.0, 0.0, 0.75), size=(0.15, 0.15, 0.15)),
    material=gs.materials.MPM.Sand(),
)

scene.build()

# simulate until piles merge and settle
for _ in range(2000):
    scene.step()
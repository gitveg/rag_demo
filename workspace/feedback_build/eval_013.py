import genesis as gs

########################## init ##########################
gs.init()

########################## create a scene ##########################
scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    mpm_options=gs.options.MPMOptions(
        lower_bound=(-0.5, -0.5, 0.0),
        upper_bound=(0.5, 0.5, 0.8),
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

########################## entities ##########################
# rigid ground
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

# soft elastic sphere using MPM
sphere = scene.add_entity(
    material=gs.materials.MPM.Elastic(),
    morph=gs.morphs.Sphere(
        pos=(0.0, 0.0, 0.5),
        radius=0.1,
    ),
    surface=gs.surfaces.Default(
        color=(0.4, 0.4, 1.0),
        vis_mode="particle",
    ),
)

########################## build and simulate ##########################
scene.build()

for _ in range(250):
    scene.step()
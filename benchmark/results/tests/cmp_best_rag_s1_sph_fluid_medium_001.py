import genesis as gs

########################## init ##########################
gs.init()

########################## create a scene ##########################
scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    sph_options=gs.options.SPHOptions(
        lower_bound=(-0.5, -0.5, 0.0),
        upper_bound=(0.5, 0.5, 1.0),
        particle_size=0.01,
    ),
    vis_options=gs.options.VisOptions(
        visualize_sph_boundary=True,
    ),
    show_viewer=True,
)

########################## entities ##########################
# static floor
floor = scene.add_entity(
    morph=gs.morphs.Plane(pos=(0.0, 0.0, 0.0), euler=(0.0, 0.0, 0.0)),
)

# slanted surface to let water flow down
ramp = scene.add_entity(
    morph=gs.morphs.Plane(pos=(0.0, 0.0, 0.15), euler=(0.0, 40.0, 0.0)),
    surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5)),
)

# column of water (stream source) above the ramp
water = scene.add_entity(
    morph=gs.morphs.Box(pos=(0.0, 0.0, 0.7), size=(0.06, 0.06, 0.3)),
    material=gs.materials.SPH.Liquid(),
    surface=gs.surfaces.Default(color=(0.2, 0.5, 1.0)),
)

########################## build and simulate ##########################
scene.build()

for _ in range(500):
    scene.step()
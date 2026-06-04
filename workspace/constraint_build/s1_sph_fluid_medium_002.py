import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    sph_options=gs.options.SPHOptions(
        lower_bound=(-1.0, -1.0, 0.0),
        upper_bound=(1.0, 1.0, 1.5),
        particle_size=0.015,
    ),
    vis_options=gs.options.VisOptions(
        visualize_sph_boundary=True,
    ),
    show_viewer=True,
)

# Bowl: a static box (rigid) that acts as a container
bowl = scene.add_entity(
    morph=gs.options.morphs.Box(
        pos=(0.0, 0.0, 0.3),
        size=(0.8, 0.8, 0.2),
    ),
    material=gs.materials.Rigid(rho=200.0),
)

# Left liquid block (stream from left side)
liquid_left = scene.add_entity(
    morph=gs.options.morphs.Box(
        pos=(-0.5, 0.0, 0.8),
        size=(0.2, 0.2, 0.2),
    ),
    material=gs.materials.SPH.Liquid(rho=1000.0, stiffness=50000.0, exponent=7.0, mu=0.005, gamma=0.01),
)

# Right liquid block (stream from right side)
liquid_right = scene.add_entity(
    morph=gs.options.morphs.Box(
        pos=(0.5, 0.0, 0.8),
        size=(0.2, 0.2, 0.2),
    ),
    material=gs.materials.SPH.Liquid(rho=1000.0, stiffness=50000.0, exponent=7.0, mu=0.005, gamma=0.01),
)

scene.build()

for i in range(500):
    scene.step()
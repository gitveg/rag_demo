import genesis as gs

gs.init()

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

# Ground plane (visual)
plane_entity = scene.add_entity(
    morph=gs.options.morphs.Plane(),
)

# Water block poured from a small height
water_entity = scene.add_entity(
    morph=gs.options.morphs.Box(
        size=(0.4, 0.4, 0.1),
        pos=(0.0, 0.0, 0.6),
    ),
    material=gs.materials.SPH.Liquid(),
)

scene.build()

# Run simulation for 500 steps
for i in range(500):
    scene.step()
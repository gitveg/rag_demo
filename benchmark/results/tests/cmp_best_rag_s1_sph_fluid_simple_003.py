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

plane = scene.add_entity(gs.morphs.Plane())
water = scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 0.5),
        size=(0.1, 0.1, 0.1),
    ),
    material=gs.materials.SPH.Liquid(),
)

scene.build()

for i in range(2000):
    scene.step()
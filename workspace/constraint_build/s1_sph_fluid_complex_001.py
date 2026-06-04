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

sphere = scene.add_entity(
    morph=gs.options.morphs.Box(size=(0.1, 0.1, 0.1), pos=(0.0, 0.0, 1.5)),
    material=gs.materials.Rigid(rho=200.0),
)

scene.build()

for i in range(500):
    scene.step()
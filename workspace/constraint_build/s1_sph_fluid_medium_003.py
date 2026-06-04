import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    sph_options=gs.options.SPHOptions(
        lower_bound=(-0.5, -0.5, -0.5),
        upper_bound=(0.5, 0.5, 0.5),
        particle_size=0.01,
    ),
    vis_options=gs.options.VisOptions(
        visualize_sph_boundary=True,
    ),
    show_viewer=True,
)

liquid_material = gs.materials.SPH.Liquid()
tank = scene.add_entity(
    morph=gs.options.morphs.Box(size=(1.0, 1.0, 0.5), pos=(0.0, 0.0, -0.25)),
    material=liquid_material,
)

scene.build()

for i in range(500):
    scene.step()
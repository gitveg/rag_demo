import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    sph_options=gs.options.SPHOptions(
        lower_bound=(-0.8, -0.8, 0.0),
        upper_bound=(0.8, 0.8, 1.5),
        particle_size=0.01,
    ),
    vis_options=gs.options.VisOptions(
        visualize_sph_boundary=True,
    ),
    show_viewer=True,
)

# Floor
scene.add_entity(
    morph=gs.morphs.Plane(),
)

# Glass container (transparent box)
scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.4),
        size=(0.4, 0.4, 0.8),
    ),
    material=gs.materials.Rigid(),
    surface=gs.surfaces.Glass(),
)

# Water emitter (faucet)
emitter = scene.add_emitter(
    material=gs.materials.SPH.Liquid(),
    max_particles=50000,
    surface=gs.surfaces.Water(),
)

scene.build()

for i in range(500):
    scene.step()
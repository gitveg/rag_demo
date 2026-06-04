import genesis as gs

gs.init(precision="32", logging_level="info")

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=1e-2,
        substeps=10,
    ),
    sph_options=gs.options.SPHOptions(
        lower_bound=(-0.5, -1.0, -0.5),
        upper_bound=(0.5, 0.0, 0.5),
    ),
)

# container domain boundaries are used (no physical walls)

# rigid sphere (approximated as a cube)
sphere = scene.add_entity(
    morph=gs.options.morphs.Box(
        pos=(0.0, 0.5, 0.0),
        size=(0.1, 0.1, 0.1),
    ),
    material=gs.materials.Rigid(),
)

# water emitter
emitter = scene.add_emitter(
    material=gs.materials.SPH.Liquid(),
    max_particles=30000,
)

scene.build()

for i in range(500):
    scene.step()
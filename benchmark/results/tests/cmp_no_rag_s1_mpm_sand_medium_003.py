import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        substeps=10,
        gravity=(0, 0, -9.81),
        dt=0.01,
    ),
    mpm_options=gs.options.MPMOptions(
        lower_bound=(-5, -5, -0.1),
        upper_bound=(5, 5, 5),
        particle_size=0.01,
    ),
)

# ground
scene.add_entity(
    gs.morphs.Box(pos=(0, 0, -0.05), size=(10, 10, 0.1)),
    material='rigid',
)

# sand block 1 from height 2.0
scene.add_entity(
    gs.morphs.Box(pos=(0, 0, 2.0), size=(0.5, 0.5, 0.5)),
    material='sand',
)

# sand block 2 from height 1.0 with slight offset
scene.add_entity(
    gs.morphs.Box(pos=(0.2, 0.2, 1.0), size=(0.5, 0.5, 0.5)),
    material='sand',
)

scene.build()

# simulate
for _ in range(500):
    scene.step()
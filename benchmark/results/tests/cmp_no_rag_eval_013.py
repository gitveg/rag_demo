import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
    ),
)

# rigid ground
ground = scene.add_entity(
    material=gs.materials.Rigid(),
    morph=gs.morphs.Box(pos=(0.0, 0.0, -0.05), size=(5.0, 0.1, 5.0)),
)

# soft elastic sphere (MPM)
sphere = scene.add_entity(
    material=gs.materials.MPM(
        E=1e5,
        nu=0.2,
        density=1000,
    ),
    morph=gs.morphs.Sphere(
        pos=(0.0, 0.5, 0.0),
        radius=0.1,
    ),
    surface=gs.surfaces.Default(),
)

scene.build()

# run simulation
for i in range(500):
    scene.step()
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        gravity=(0.0, 0.0, -9.81),
    ),
)

plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

cube = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 2.0),
        size=(0.2, 0.2, 0.2),
    ),
    material=gs.materials.FEM.Elastic(
        E=1e5,
        nu=0.3,
        rho=1000.0,
    ),
)

scene.build()

for _ in range(600):
    scene.step()
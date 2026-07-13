import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
        gravity=(0, 0, -9.81),
    ),
)

plane = scene.add_entity(morph=gs.morphs.Plane())

cube = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0, 0, 0.5),
        size=(0.2, 0.2, 0.2),
    ),
    material=gs.materials.FEM.Elastic(
        E=1e5,
        nu=0.3,
        rho=1000,
    ),
)

sphere = scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(0, 0, 1.0),
        radius=0.1,
    ),
    material=gs.materials.Rigid(rho=1000),
)

scene.build()

for _ in range(300):
    scene.step()
import genesis as gs

gs.init()

scene = gs.Scene()

floor = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid()
)

cube_soft = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 0.5), size=(0.1, 0.1, 0.1)),
    material=gs.materials.FEM.Elastic(E=1e3, nu=0.3, rho=1000)
)

cube_stiff = scene.add_entity(
    gs.morphs.Box(pos=(0.2, 0.0, 0.5), size=(0.1, 0.1, 0.1)),
    material=gs.materials.FEM.Elastic(E=1e4, nu=0.3, rho=1000)
)

scene.build()

for _ in range(1000):
    scene.step()
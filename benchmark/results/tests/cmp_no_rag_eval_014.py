import genesis as gs

gs.init()

scene = gs.Scene()

# Static rigid bottom box (larger)
bottom_box = scene.add_entity(
    material=gs.materials.Rigid(),
    morph=gs.morphs.Box(pos=(0, 0, 0.2), size=(1.0, 1.0, 0.2)),
    fixed=True,
)

# Elastic soft top box (smaller)
top_box = scene.add_entity(
    material=gs.materials.FEM.Elastic(youngs_modulus=1e5, poisson_ratio=0.3),
    morph=gs.morphs.Box(pos=(0, 0, 0.45), size=(0.3, 0.3, 0.3)),
)

scene.build()

for _ in range(200):
    scene.step()
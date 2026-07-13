import genesis as gs

gs.init()

scene = gs.Scene(
    show_viewer=True,
)

# Large static sphere at the origin
scene.add_entity(
    gs.morphs.Sphere(radius=1.0, pos=(0.0, 0.0, 0.0)),
    material=gs.materials.Rigid(fixed=True),
)

# Small box above the sphere
scene.add_entity(
    gs.morphs.Box(size=(0.3, 0.3, 0.3), pos=(0.0, 0.0, 2.0)),
    material=gs.materials.Rigid(),
)

scene.build()

for _ in range(1000):
    scene.step()
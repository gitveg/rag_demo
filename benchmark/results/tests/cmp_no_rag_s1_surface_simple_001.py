import genesis as gs

gs.init()

scene = gs.Scene()

scene.add_entity(gs.morphs.Plane())

scene.add_entity(
    gs.morphs.Sphere(
        pos=(0, 0, 1.0),
        radius=0.5,
    ),
    material=gs.materials.Rigid(color=(0, 0, 1, 1)),
)

scene.build()

for _ in range(1000):
    scene.step()
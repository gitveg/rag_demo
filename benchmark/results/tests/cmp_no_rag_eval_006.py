import genesis as gs

gs.init()

scene = gs.Scene()

plane = scene.add_entity(gs.morphs.Plane())

sphere1 = scene.add_entity(
    gs.morphs.Sphere(pos=(-1.0, 0.0, 2.0), radius=0.5),
    material=gs.materials.Rigid(),
)

sphere2 = scene.add_entity(
    gs.morphs.Sphere(pos=(1.0, 0.0, 2.0), radius=0.5),
    material=gs.materials.Rigid(),
)

scene.build()

for _ in range(500):
    scene.step()
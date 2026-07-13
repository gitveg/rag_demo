import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(
    gs.morphs.Plane(),
)

cylinder = scene.add_entity(
    gs.morphs.Cylinder(
        pos=(0.0, 0.0, 3.0),
        radius=0.3,
        height=0.5,
    ),
)

scene.build()

for i in range(1000):
    scene.step()
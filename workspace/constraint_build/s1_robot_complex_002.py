import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(
    gs.morphs.Plane(),
)
humanoid = scene.add_entity(
    gs.morphs.MJCF(file="xml/humanoid/humanoid.xml"),
)

scene.build()
for i in range(1000):
    scene.step()
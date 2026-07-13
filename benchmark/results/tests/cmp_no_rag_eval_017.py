import genesis as gs

gs.init()
scene = gs.Scene()

plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(gs.morphs.Franka())
box = scene.add_entity(
    gs.morphs.Box(pos=(0.5, 0.0, 0.2), size=(0.05, 0.05, 0.05)),
    material=gs.materials.Rigid(),
    color='red'
)

scene.build()
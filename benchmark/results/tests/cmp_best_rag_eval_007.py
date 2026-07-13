import genesis as gs

gs.init()

scene = gs.Scene()

# Add a static ground plane
plane = scene.add_entity(gs.morphs.Plane())

# Stack three boxes vertically
box_bottom = scene.add_entity(
    gs.morphs.Box(size=(0.2, 0.2, 0.2), pos=(0, 0, 0.1))
)
box_middle = scene.add_entity(
    gs.morphs.Box(size=(0.2, 0.2, 0.2), pos=(0, 0, 0.3))
)
box_top = scene.add_entity(
    gs.morphs.Box(size=(0.2, 0.2, 0.2), pos=(0, 0, 0.5))
)

scene.build()

for _ in range(1000):
    scene.step()
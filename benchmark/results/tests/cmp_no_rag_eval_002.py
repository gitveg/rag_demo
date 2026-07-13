import genesis as gs

gs.init()
scene = gs.Scene()

# Create a static rigid box obstacle
box = scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 0.5),
        size=(1.0, 1.0, 1.0),
    ),
    fixed=True,
)

scene.build()

# A few simulation steps to finalize the scene
for _ in range(10):
    scene.step()
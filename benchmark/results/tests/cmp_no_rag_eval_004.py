import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        gravity=(0.0, 0.0, 0.0),
    ),
)

box = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.0),
        size=(0.2, 0.2, 0.2),
    ),
)

scene.build()

for _ in range(1000):
    scene.step()
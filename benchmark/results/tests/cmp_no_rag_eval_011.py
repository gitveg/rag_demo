import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        gravity=(0, 0, 0),
    ),
)

plane = scene.add_entity(gs.morphs.Plane())
box0 = scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 0.5),
        size=(0.2, 0.2, 0.2),
    )
)
box1 = scene.add_entity(
    gs.morphs.Box(
        pos=(0.25, 0.0, 0.5),
        size=(0.2, 0.2, 0.2),
    )
)

scene.build()

# give the first box a gentle push towards the second
box0.set_dofs_velocity([0.05, 0.0, 0.0, 0.0, 0.0, 0.0])

# run a few simulation steps to let them collide
for _ in range(200):
    scene.step()
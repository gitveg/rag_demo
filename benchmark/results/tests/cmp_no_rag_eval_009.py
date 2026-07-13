import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
)

# ground plane
plane = scene.add_entity(gs.morphs.Plane())

# red rigid box
box = scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 2.0),
        size=(0.2, 0.2, 0.2),
    ),
    surface=gs.surfaces.Default(color=(1, 0, 0, 1)),
)

# blue rigid cylinder
cylinder = scene.add_entity(
    gs.morphs.Cylinder(
        pos=(0.5, 0.0, 2.0),
        radius=0.1,
        height=0.3,
    ),
    surface=gs.surfaces.Default(color=(0, 0, 1, 1)),
)

scene.build()

# drop simultaneously
for _ in range(300):
    scene.step()
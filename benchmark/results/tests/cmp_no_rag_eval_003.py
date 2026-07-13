import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
        gravity=(0, 0, -9.81),
    ),
    show_viewer=True,
)

plane = scene.add_entity(
    gs.morphs.Plane(),
)

cylinder = scene.add_entity(
    gs.morphs.Cylinder(
        pos=(0.0, 0.0, 3.5),
        radius=0.3,
        height=1.0,
    ),
    material=gs.materials.Rigid(),
)

scene.build()

for _ in range(500):
    scene.step()
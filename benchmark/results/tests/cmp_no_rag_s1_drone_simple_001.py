import genesis as gs

gs.init()

scene = gs.Scene(
    gravity=(0, 0, -9.81),
    show_viewer=False,
)

drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
    ),
    pos=(0, 0, 1.0),
)

scene.build()

for _ in range(1000):
    scene.step()
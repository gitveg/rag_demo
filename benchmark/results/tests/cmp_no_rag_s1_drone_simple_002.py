import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        gravity=(0, 0, -9.81),
    ),
    show_viewer=True,
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3, 0, 2),
        camera_lookat=(0, 0, 1),
    ),
)

plane = scene.add_entity(gs.morphs.Plane())
drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
    ),
)

scene.build()

target_height = 1.5

for i in range(2000):
    drone.set_target_position([0, 0, target_height])
    scene.step()
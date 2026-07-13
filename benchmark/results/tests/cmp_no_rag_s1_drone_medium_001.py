import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    show_viewer=True,
)

plane = scene.add_entity(gs.morphs.Plane())
drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
    ),
)

# Take off to 2 meters
drone.ctrl.set_pose(pos=(0, 0, 2))
for _ in range(200):   # 2 s * 100 Hz
    scene.step()

# Hover for 3 seconds
for _ in range(300):
    scene.step()

# Land back down
drone.ctrl.set_pose(pos=(0, 0, 0))
for _ in range(200):
    scene.step()
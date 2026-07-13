import genesis as gs
import numpy as np

gs.init(backend=gs.cpu)

scene = gs.Scene(
    show_viewer=True,
    rigid_options=gs.options.RigidOptions(
        dt=0.01,
    ),
)

drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
    ),
)

scene.build()

# takeoff to 1 meter
target_pos = np.array([0.0, 0.0, 1.0])
target_yaw = 0.0
for _ in range(200):
    drone.control(pos=target_pos, yaw=target_yaw)
    scene.step()

# square path: 4 times (forward 3m, turn right 90 deg)
current_pos = target_pos.copy()
current_yaw = 0.0
for _ in range(4):
    # move forward 3m
    forward = np.array([np.cos(current_yaw), np.sin(current_yaw), 0.0])
    next_pos = current_pos + forward * 3.0
    for _ in range(300):
        drone.control(pos=next_pos, yaw=current_yaw)
        scene.step()
    current_pos = next_pos

    # turn right 90 deg
    current_yaw -= np.pi / 2.0
    for _ in range(200):
        drone.control(pos=current_pos, yaw=current_yaw)
        scene.step()

# land (descend vertically)
land_pos = np.array([current_pos[0], current_pos[1], 0.0])
for _ in range(200):
    drone.control(pos=land_pos, yaw=current_yaw)
    scene.step()

# keep viewer open
while True:
    scene.step()
import genesis as gs
import numpy as np

gs.init(backend=gs.gpu)

scene = gs.Scene(
    show_viewer=True,
)

# Ground plane
plane = scene.add_entity(
    gs.morphs.Plane(),
)

# Crazyflie 2.X drone
drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
    ),
    pos=(0.0, 0.0, 0.1),
    fixed=True,  # set kinematic so we can directly teleport for demo
)

# Upright hoops as thin tori
hoop_morph = gs.morphs.Torus(
    R=0.5,         # ring radius
    r=0.02,        # cross-section radius
)

# Place three hoops at different heights, facing forward (upright)
hoop1 = scene.add_entity(hoop_morph, pos=(2.0, 0.0, 1.0), fixed=True)
hoop2 = scene.add_entity(hoop_morph, pos=(4.0, 0.0, 1.5), fixed=True)
hoop3 = scene.add_entity(hoop_morph, pos=(6.0, 0.0, 2.0), fixed=True)

# Camera view
scene.cam.set_lookat(
    pos=(4.0, -6.0, 3.0),
    tar=(4.0, 0.0, 1.5),
    up=(0.0, 0.0, 1.0),
)

# Simple waypoints (drone passes through each hoop center and then lands)
# Format: [time, position_x, position_y, position_z]
waypoints = [
    (0.0, 0.0, 0.0, 0.1),      # start low
    (2.0, 2.0, 0.0, 1.0),      # through hoop1
    (3.0, 4.0, 0.0, 1.5),      # through hoop2
    (4.0, 6.0, 0.0, 2.0),      # through hoop3
    (5.0, 7.0, 0.0, 1.5),      # begin descent
    (6.0, 8.0, 0.0, 0.3),      # near ground
    (7.0, 8.5, 0.0, 0.05),     # landed
]
waypoints = np.array(waypoints)

# Simulation loop
t = 0.0
sim_time = 7.0
while t < sim_time:
    t = scene.cur_t  # current simulation time

    # Interpolate position from waypoints
    if t <= waypoints[0, 0]:
        idx = 0
        alpha = 0
    elif t >= waypoints[-1, 0]:
        idx = len(waypoints) - 2
        alpha = 1.0
    else:
        for i in range(len(waypoints) - 1):
            if waypoints[i, 0] <= t <= waypoints[i + 1, 0]:
                idx = i
                dt = waypoints[i + 1, 0] - waypoints[i, 0]
                alpha = (t - waypoints[i, 0]) / dt if dt > 0 else 0
                break

    pos = waypoints[idx, 1:] * (1 - alpha) + waypoints[idx + 1, 1:] * alpha

    # Keep drone level, no rotation
    drone.set_pose(gs.Pose(p=pos, q=gs.quat_from_euler(0.0, 0.0, 0.0)))

    scene.step()

# Land safely: we already ended at landed position, but hold a bit
# Wait a few extra steps
for _ in range(100):
    scene.step()
    drone.set_pose(gs.Pose(p=(8.5, 0.0, 0.05), q=gs.quat_from_euler(0.0, 0.0, 0.0)))

# Keep viewer open (optional)
scene.viewer.stop()
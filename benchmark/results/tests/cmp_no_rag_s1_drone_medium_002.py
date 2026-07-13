import numpy as np
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(camera_fov=40),
)

# Add Crazyflie drone
drone = scene.add_entity(
    gs.morphs.Drone(file="urdf/drones/cf2p.urdf", model="CF2P"),
    pos=(0.0, 0.0, 0.02),
)

# Add visual markers for checkpoints
checkpoints = [
    (1.0, 0.0, 0.5),
    (2.0, 0.0, 0.5),
    (3.0, 0.0, 0.5),
]
for wp in checkpoints:
    scene.add_entity(
        gs.morphs.Sphere(pos=wp, radius=0.05, color=(1.0, 0.0, 0.0))
    )
land_marker = scene.add_entity(
    gs.morphs.Sphere(pos=(4.0, 0.0, 0.0), radius=0.05, color=(0.0, 1.0, 0.0))
)

scene.build()
sim = scene.sim

takeoff_height = 0.5
target_land = (4.0, 0.0, 0.0)
state = "takeoff"
wp_index = 0

# Simulation loop
while True:
    pos = drone.get_pos()
    if state == "takeoff":
        target = (0.0, 0.0, takeoff_height)
        if np.linalg.norm(pos - np.array(target)) < 0.05:
            state = "waypoints"
            wp_index = 0
    elif state == "waypoints":
        if wp_index < len(checkpoints):
            target = checkpoints[wp_index]
            if np.linalg.norm(pos - np.array(target)) < 0.05:
                wp_index += 1
                if wp_index >= len(checkpoints):
                    state = "land"
        else:
            state = "land"
    elif state == "land":
        target = target_land
        if np.linalg.norm(pos - np.array(target)) < 0.05:
            # Landed successfully; hold position
            pass

    drone.set_pid_target(pos=target)
    sim.step()
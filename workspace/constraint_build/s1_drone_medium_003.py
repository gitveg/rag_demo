import argparse
import threading

import numpy as np
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(2.5, 0.0, 1.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
        max_FPS=60,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        show_viewer=args.vis,
    )

    ########################## add entities ##########################
    # Ground
    plane = scene.add_entity(gs.morphs.Plane())

    # Drone
    drone = scene.add_entity(
        gs.morphs.Drone(),
        material=gs.materials.Rigid(),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## circular trajectory parameters ##########################
    radius = 2.0          # meters
    altitude = 1.0        # meters (maintain this height)
    ang_speed = 0.5       # rad/s
    dt = 1.0 / 60.0       # simulation step
    t = 0.0

    ########################## simulation loop ##########################
    while True:
        # Compute desired position on the horizontal circle
        x = radius * np.cos(ang_speed * t)
        y = radius * np.sin(ang_speed * t)
        z = altitude
        desired_pos = np.array([x, y, z])

        # Command the drone to that position (kinematic set)
        drone.set_pos(desired_pos)

        # Advance simulation
        scene.step()
        t += dt


if __name__ == "__main__":
    main()
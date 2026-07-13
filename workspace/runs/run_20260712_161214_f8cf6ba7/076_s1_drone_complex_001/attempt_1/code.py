import argparse
import numpy as np

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    # init
    gs.init(backend=gs.cpu)

    # viewer options
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(2.5, 0.0, 1.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
        max_FPS=60,
    )

    # scene
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=0.01),
        viewer_options=viewer_options,
        show_viewer=args.vis,
    )

    # entities
    plane = scene.add_entity(gs.morphs.Plane())
    drone = scene.add_entity(
        gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            pos=(0.0, 0.0, 0.5),
            model="CF2X",
        ),
    )

    # build scene
    scene.build()

    # initial hover at starting position
    target_pos = drone.get_pos().copy()
    target_yaw = 0.0
    drone.control(pos=target_pos, yaw=target_yaw)

    # define square path waypoints (3 m side, right turns)
    side = 3.0
    # yaw for each direction after turns: start 0, then -90, -180, -270
    yaw_sequence = [0.0, -np.pi / 2, -np.pi, -3 * np.pi / 2]

    # compute world-frame target positions for the four corners
    # start at (0,0,0.5), move forward (+x) when yaw=0, then right etc.
    positions = [target_pos]
    for yaw in yaw_sequence:
        forward = np.array([np.cos(yaw), np.sin(yaw), 0.0])
        next_pos = positions[-1] + forward * side
        positions.append(next_pos)

    # landing position (z=0.0)
    landing_pos = np.array([positions[-1][0], positions[-1][1], 0.0])

    waypoints = list(zip(positions[1:], yaw_sequence))  # the four sides
    waypoints.append((landing_pos, 0.0))                 # land with yaw=0

    # fly waypoint to waypoint
    for wp_pos, wp_yaw in waypoints:
        drone.control(pos=wp_pos, yaw=wp_yaw)
        # wait until within tolerance
        for _ in range(1000):
            scene.step()
            cur_pos = drone.get_pos()
            if np.linalg.norm(cur_pos - wp_pos) < 0.1:
                break

    # extra settling time
    for _ in range(200):
        scene.step()

    # cleanup viewer if used
    if args.vis:
        scene.viewer.stop()


if __name__ == "__main__":
    main()
import argparse
import numpy as np

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=True)
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
        show_FPS=True,
    )

    ########################## add entities ##########################
    # ground plane
    plane = scene.add_entity(morph=gs.morphs.Plane())
    # drone (quadcopter)
    drone = scene.add_entity(morph=gs.morphs.Drone())

    ########################## build scene ##########################
    scene.build()

    ########################## control loop ##########################
    # motor thrust range: typically 0–1 (normalized) or N? We'll use normalized.
    # hover_thrust = 0.7 (approximate for drone mass)
    hover_thrust = 0.7
    climb_thrust = 0.85  # slightly above hover to climb
    target_height = 1.0

    # main simulation loop
    for i in range(1000):
        # get current height
        pos = drone.get_pos()
        height = pos[2]

        if height < target_height - 0.05:
            # climbing phase
            motor_values = np.array([climb_thrust, climb_thrust, climb_thrust, climb_thrust])
        else:
            # hover at target height
            motor_values = np.array([hover_thrust, hover_thrust, hover_thrust, hover_thrust])

        # set motor commands
        drone.set_motors(motor_values)

        # step simulation
        scene.step()

        if args.vis and i % 10 == 0:
            print(f"Height: {height:.3f} m")


if __name__ == "__main__":
    main()
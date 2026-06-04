import argparse
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
        camera_pos=(5.0, 5.0, 5.0),
        camera_lookat=(0.0, 0.0, 2.0),
        camera_fov=30,
        max_FPS=60,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        show_viewer=args.vis,
    )

    ########################## add entities ##########################
    # ground plane
    plane = scene.add_entity(
        morph=gs.morphs.Plane(),
    )

    # drone
    drone = scene.add_entity(
        morph=gs.morphs.Drone(),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## control the drone ##########################
    # set initial position (above ground)
    qpos = drone.get_qpos()
    qpos[0] = 0.0   # x
    qpos[1] = 0.0   # y
    qpos[2] = 2.0   # z (height)
    drone.set_qpos(qpos)

    # define a simple trajectory: figure-8 pattern
    t = 0.0
    dt = 1e-2
    while t < 10.0:
        # target positions
        x_des = 2.0 * np.sin(2.0 * t)
        y_des = 2.0 * np.sin(4.0 * t)
        z_des = 2.0 + 0.5 * np.sin(1.0 * t)

        # compute desired velocity (proportional control)
        pos = drone.get_qpos()[:3]
        vel_des = 2.0 * (np.array([x_des, y_des, z_des]) - pos)

        # set motor velocities (simple inverse)
        # drone has 4 rotors; we just set the whole body velocity
        # this is a simplified control – using a built-in PID would be better
        # but we just apply forces directly
        # For a real drone, we would compute rotor speeds; here we set joint velocities
        drone.control_dofs_velocity(
            vel_des[0] * np.ones(4),  # placeholder, not accurate
        )

        # step simulation
        scene.step()

        # simple collision avoidance: if too low, push up
        if pos[2] < 1.0:
            drone.set_qpos(qpos[:2].tolist() + [1.5])

        t += dt

if __name__ == "__main__":
    main()
import argparse

import numpy as np

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, -3.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=args.vis,
        show_FPS=True,
    )

    ########################## add entities ##########################
    # URDF file path
    urdf_path = "robot.urdf"
    robot = scene.add_entity(
        morph=gs.morphs.URDF(file=urdf_path),
    )

    ########################## build ##########################
    scene.build()

    ########################## set joints to zero position ##########################
    # Get number of joints (dofs)
    n_dofs = robot.n_dofs
    zero_pos = np.zeros(n_dofs)
    robot.set_qpos(zero_pos)
    robot.forward_dynamics()

    # If visualization, run a few steps
    if args.vis:
        for i in range(200):
            scene.step()

    print("Robotic arm loaded and joints set to zero position.")


if __name__ == "__main__":
    main()
import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.0, -2, 1.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    ########################## add robot arm ##########################
    # Replace with your actual URDF file path
    urdf_path = "path/to/robot.urdf"
    robot = scene.add_entity(
        morph=gs.options.morphs.URDF(file=urdf_path, pos=(0.0, 0.0, 0.0)),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## set first joint to 45 degrees ##########################
    # Assume first joint is index 0; adjust if needed.
    target_angle = 45.0  # degrees
    # Convert to radians if necessary (Genesis expects radians)
    target_angle_rad = target_angle * 3.141592653589793 / 180.0

    # Use position control to move the joint
    robot.control_dofs_position(
        position=[target_angle_rad],
        dofs_idx=[0],
    )

    ########################## simulation loop ##########################
    for i in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
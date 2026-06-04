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
            camera_pos=(0.0, -2, 1.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    ########################## add entities ##########################
    # ground plane
    plane = scene.add_entity(gs.morphs.Plane())
    # quadruped robot (Unitree Go2)
    robot = scene.add_entity(
        gs.morphs.URDF(
            file="urdf/go2/urdf/go2.urdf",
            pos=(0.0, 0.0, 0.65),
            euler=(0.0, 0.0, 0.0),
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build ##########################
    scene.build()

    # get joint names
    joint_names = robot.get_joint_names()
    print("Joint names:", joint_names)

    # identify front leg joints (example: FL_hip, FL_thigh, FL_knee, FR_hip, FR_thigh, FR_knee)
    # adjust based on actual URDF joint names
    front_left_joints = [n for n in joint_names if "FL_" in n or "front_left" in n.lower()]
    front_right_joints = [n for n in joint_names if "FR_" in n or "front_right" in n.lower()]
    # if not found, try alternative naming
    if not front_left_joints:
        front_left_joints = [n for n in joint_names if "leg1" in n.lower()]  # fallback
    if not front_right_joints:
        front_right_joints = [n for n in joint_names if "leg0" in n.lower()]  # fallback
    print("Front left joints:", front_left_joints)
    print("Front right joints:", front_right_joints)

    # define lifting poses (approximate, adjust as needed)
    # lifting front left leg: bend knee and lift thigh
    lift_left_targets = {
        "FL_knee_joint": -0.8,
        "FL_thigh_joint": 0.3,
        "FL_hip_joint": 0.0,
        # keep other joints at current (or zero)
    }
    lift_right_targets = {
        "FR_knee_joint": -0.8,
        "FR_thigh_joint": 0.3,
        "FR_hip_joint": 0.0,
    }
    # standing neutral (all joints at zero)
    neutral_targets = {j: 0.0 for j in joint_names}

    ########################## simulate lifting sequence ##########################
    for step_count in range(500):
        # time in seconds (step dt is 0.01 by default)
        t = step_count * scene.dt

        # sequence: first 1 sec neutral, then lift left for 2 sec, then neutral, then lift right for 2 sec, etc.
        if t < 1.0:
            targets = neutral_targets
        elif t < 3.0:
            targets = {**neutral_targets, **lift_left_targets}
        elif t < 4.0:
            targets = neutral_targets
        elif t < 6.0:
            targets = {**neutral_targets, **lift_right_targets}
        else:
            targets = neutral_targets

        # apply control
        robot.control_joint_position(targets)
        scene.step()


if __name__ == "__main__":
    main()
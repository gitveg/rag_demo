import argparse
import os
import sys
import numpy as np
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="64")

    ########################## create scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1.0 / 60,
            substeps=2,
        ),
        rigid_options=gs.options.RigidOptions(
            enable_collision=True,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, -1.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=args.vis,
        show_FPS=False,
    )

    ########################## add entities ##########################
    # Franka arm
    robot = scene.add_entity(
        morph=gs.options.morphs.MJCF(
            file="franka_lab/franka_alt_obj.xml",
        ),
        material=gs.materials.Rigid(),
    )

    # Rigid sphere on the ground
    sphere = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            radius=0.1,
            pos=(0.0, 0.0, 0.1),
        ),
        material=gs.materials.Rigid(rho=500.0),
    )

    # Cloth as a soft sphere (piece of cloth)
    cloth = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            radius=0.15,
            pos=(0.5, 0.0, 0.3),
        ),
        material=gs.materials.FEM.Cloth(),
        surface=gs.surfaces.Default(
            color=(0.8, 0.2, 0.2, 1.0),
        ),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## get arm end effector ##########################
    end_effector = robot.get_link("hand")

    ########################## control loop ##########################
    # In this example we simply lift the cloth above the sphere
    # using a motion plan with inverse kinematics.

    # Target grasp position (above cloth)
    grasp_pos = np.array([0.5, 0.0, 0.35])
    lift_pos = np.array([0.0, 0.0, 0.6])  # above sphere

    # Move to grasp
    for _ in range(200):
        # Compute IK for the end effector
        q = robot.inverse_kinematics(
            link=end_effector,
            pos=grasp_pos,
            quat=np.array([1.0, 0.0, 0.0, 0.0]),
        )
        robot.control_dofs_position(q, enable_ik=True)
        scene.step()

    # Close gripper (simulate by setting finger joint positions)
    # In Franka, finger joints are typically "left_finger" and "right_finger"
    # Opening: both closed to 0.04, closing: 0.0 (or slightly negative)
    # We'll close them over a few steps
    for _ in range(50):
        robot.control_dofs_position(
            {
                "left_finger": 0.0,
                "right_finger": 0.0,
            },
            enable_ik=False,
        )
        scene.step()

    # Lift to above sphere
    for _ in range(200):
        q = robot.inverse_kinematics(
            link=end_effector,
            pos=lift_pos,
            quat=np.array([1.0, 0.0, 0.0, 0.0]),
        )
        robot.control_dofs_position(q, enable_ik=True)
        scene.step()

    # Open gripper to release cloth
    for _ in range(50):
        robot.control_dofs_position(
            {
                "left_finger": 0.04,
                "right_finger": 0.04,
            },
            enable_ik=False,
        )
        scene.step()

    # Let simulation run a bit for drape effect
    for _ in range(200):
        scene.step()

    print("Simulation finished.")


if __name__ == "__main__":
    main()
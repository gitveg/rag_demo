import argparse
import os

import numpy as np

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    parser.add_argument("--horizon", type=int, default=500 if "PYTEST_VERSION" not in os.environ else 25)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="32", logging_level="info")

    dt: float = 1e-2
    particle_size: float = 1e-2

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=dt,
            substeps=10,
        ),
        pbd_options=gs.options.PBDOptions(
            particle_size=particle_size,
        ),
        viewer_options=gs.options.ViewerOptions(),
        show_viewer=args.vis,
    )

    # Table
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, -0.05),
            size=(1.2, 1.2, 0.1),
            fixed=True,
        ),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5, 1.0)),
    )

    # Sphere resting on the table
    sphere = scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 0.1),
            radius=0.1,
        ),
        surface=gs.surfaces.Default(color=(0.3, 0.3, 1.0, 1.0)),
    )

    # Cloth (replace with your own mesh file)
    cloth = scene.add_entity(
        material=gs.materials.PBD.Cloth(),
        morph=gs.morphs.Mesh(
            file="meshes/cloth.obj",
            scale=1.0,
            pos=(0.3, 0.0, 0.15),
            euler=(0.0, 0.0, 0.0),
        ),
        surface=gs.surfaces.Default(
            color=(0.8, 0.4, 0.2, 1.0),
            vis_mode="visual",
        ),
    )

    # Robotic arm (Franka panda as an example)
    robot = scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.MJCF(
            file="xml/franka_emika_panda/mjcf.xml",
            pos=(0.35, 0.0, 0.0),
            euler=(0.0, 0.0, 0.0),
        ),
        surface=gs.surfaces.Default(color=(0.2, 0.8, 0.2, 1.0)),
    )

    scene.build()

    # Identify gripper and arm joint indices
    n_dofs = robot.n_dofs
    dof_names = robot.dof_names
    print("Robot DOFs:", dof_names)

    finger_idx = [i for i, name in enumerate(dof_names) if "finger" in name.lower()]
    arm_idx = [i for i in range(n_dofs) if i not in finger_idx]

    # Define key poses (arm joints only; fingers controlled separately)
    # all arm joints zero for simplicity, adjust as needed
    start_pose = np.zeros(len(arm_idx))
    grasp_pose = np.array([0.0, -0.3, 0.0, -1.2, 0.0, 1.0, 0.5])  # reach cloth
    lift_pose = np.array([0.0, -0.8, 0.0, -1.5, 0.0, 1.2, 0.8])   # lift up
    above_sphere_pose = np.array([-0.3, -0.8, 0.0, -1.5, 0.0, 1.2, 0.8])  # move over sphere

    # Trajectory with time phases
    for i in range(args.horizon):
        t = i * dt

        # Get current target arm joints (last commanded)
        current_arm = robot.get_dofs_position()[arm_idx].cpu().numpy()

        if t < 1.0:
            alpha = t / 1.0
            target_arm = alpha * grasp_pose + (1.0 - alpha) * start_pose
            target_fingers = np.zeros(len(finger_idx))  # open
        elif t < 1.5:
            target_arm = grasp_pose.copy()
            target_fingers = np.ones(len(finger_idx)) * 0.04  # close
        elif t < 3.0:
            alpha = (t - 1.5) / 1.5
            target_arm = (1.0 - alpha) * grasp_pose + alpha * lift_pose
            target_fingers = np.ones(len(finger_idx)) * 0.04
        elif t < 4.5:
            alpha = (t - 3.0) / 1.5
            target_arm = (1.0 - alpha) * lift_pose + alpha * above_sphere_pose
            target_fingers = np.ones(len(finger_idx)) * 0.04
        elif t < 5.0:
            target_arm = above_sphere_pose.copy()
            target_fingers = np.zeros(len(finger_idx))  # open
        else:
            target_arm = above_sphere_pose.copy()
            target_fingers = np.zeros(len(finger_idx))

        # Set joint positions
        dofs_target = np.zeros(n_dofs)
        dofs_target[arm_idx] = target_arm
        dofs_target[finger_idx] = target_fingers
        robot.set_dofs_position(dofs_target)

        scene.step()

    if args.vis:
        scene.viewer.stop()


if __name__ == "__main__":
    main()
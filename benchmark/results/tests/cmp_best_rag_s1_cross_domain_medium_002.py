import argparse
import os

import numpy as np

import genesis as gs
import genesis.utils.geom as gu


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="32", logging_level="info")

    # download genesis assets if not already present
    if "GENESIS_HOME" not in os.environ:
        os.environ["GENESIS_HOME"] = os.path.join(os.path.expanduser("~"), "genesis")
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id="Genesis-Dev/genesis",
        local_dir=os.environ["GENESIS_HOME"],
        ignore_patterns=[],
    )

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=2e-3,
            substeps=10,
        ),
        pbd_options=gs.options.PBDOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, -1.5, 1.5),
            camera_lookat=(0.5, 0.5, 0.4),
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # table
    scene.add_entity(morph=gs.morphs.Plane())

    # rigid sphere resting on table
    sphere_pos = np.array([0.7, 0.5, 0.07])  # radius 0.05, placed on table z=0
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(pos=sphere_pos, radius=0.05),
        material=gs.materials.Rigid(),
    )

    # cloth placed on table
    cloth = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=os.path.join(os.environ["GENESIS_HOME"], "assets/meshes/cloth.obj"),
            pos=(0.3, 0.5, 0.02),
            scale=0.1,
            euler=(0.0, 0.0, 0.0),
        ),
        material=gs.materials.PBD.Cloth(),
    )

    # Franka arm
    franka = scene.add_entity(
        morph=gs.morphs.MJCF(file="xml/franka_emika_panda/scene.xml"),
    )

    ########################## build ##########################
    scene.build()

    # get links and keys
    hand_link = franka.get_link("hand")
    arm_dofs = list(range(7))   # 7 arm joints
    finger_dofs = [7, 8]        # gripper fingers (1 DOF each)

    gripper_open = 0.04
    gripper_close = 0.0

    # pre-grasp, grasp, lift, move, place positions
    pre_grasp_pos = np.array([0.3, 0.5, 0.25])   # above cloth
    grasp_pos = np.array([0.3, 0.5, 0.12])        # close to cloth
    lift_pos = np.array([0.3, 0.5, 0.35])         # lifted high
    place_pos = np.array([0.7, 0.5, 0.18])         # above sphere

    orientation = gu.quat_from_euler([0.0, np.deg2rad(180), 0.0])  # pointing downward

    # simulation phases (step counts)
    total_steps = 3000
    steps_approach = 500
    steps_grasp = 800
    steps_lift = 1100
    steps_move = 1500
    steps_place = 1900
    steps_release = 2100

    for i in range(total_steps):
        if i < steps_approach:
            target_pos = pre_grasp_pos
            fingers = gripper_open
        elif i < steps_grasp:
            target_pos = grasp_pos
            # close gripper at the end of this phase
            fingers = gripper_open if i < steps_grasp - 100 else gripper_close
        elif i < steps_lift:
            target_pos = lift_pos
            fingers = gripper_close
        elif i < steps_move:
            # blend from lift_pos to place_pos horizontally
            alpha = (i - steps_lift) / (steps_move - steps_lift)
            target_pos = (1 - alpha) * lift_pos + alpha * place_pos
            fingers = gripper_close
        elif i < steps_place:
            target_pos = place_pos
            fingers = gripper_close
        elif i < steps_release:
            target_pos = place_pos
            fingers = gripper_open   # release
        else:
            target_pos = lift_pos    # retract
            fingers = gripper_open

        # inverse kinematics
        q_arm = franka.inverse_kinematics(hand_link, target_pos, orientation)
        franka.control_dofs_position(q_arm, arm_dofs)
        franka.control_dofs_position([fingers] * 2, finger_dofs)

        scene.step()

    # final settling
    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
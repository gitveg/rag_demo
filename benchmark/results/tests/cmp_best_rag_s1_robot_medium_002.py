import numpy as np
import genesis as gs


def main():
    # Initialize Genesis with GPU backend and 32-bit precision
    gs.init(backend=gs.gpu, precision="32")

    # Create scene with viewer and simulation options
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -1, 1.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=30,
            res=(960, 640),
        ),
        rigid_options=gs.options.RigidOptions(
            dt=0.005,
        ),
        sim_options=gs.options.SimOptions(
            dt=0.005,
        ),
    )

    # Add a ground plane
    plane = scene.add_entity(gs.morphs.Plane())

    # Add Franka Panda arm
    franka = scene.add_entity(
        gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
    )

    # Joint indices
    dofs_arm = [franka.jnt_names.index(f"joint{i}") for i in range(1, 8)]
    dofs_finger = [
        franka.jnt_names.index("finger_joint1"),
        franka.jnt_names.index("finger_joint2"),
    ]

    # Small cube to pick up
    cube_size = 0.04
    cube = scene.add_entity(
        gs.morphs.Box(
            pos=(0.35, 0.2, cube_size / 2),  # sitting on the plane
            size=(cube_size, cube_size, cube_size),
        ),
        material=gs.materials.Rigid(),
    )

    # Platform where the cube will be placed (raised surface)
    platform = scene.add_entity(
        gs.morphs.Box(
            pos=(0.6, 0.2, 0.025),  # center z = 0.025, height = 0.05
            size=(0.15, 0.15, 0.05),
        ),
        material=gs.materials.Rigid(),
    )

    # Build the scene
    scene.build()

    # ============================================================
    # Pre‑defined joint angle waypoints (feel free to tune these)
    # ============================================================
    # Starting home pose (from the reference example)
    home_pose = np.array([0, -0.25, 0, -2.5, 0, 2.0, 0.8])
    # Pose ready to approach the cube
    pre_grasp_pose = np.array([0, -0.5, 0, -2.0, 0, 1.8, 0.8])
    # Lowered to gently touch / surround the cube
    grasp_pose = np.array([0, -0.5, 0, -1.5, 0, 1.8, 0.8])
    # Pose above the target platform
    pre_place_pose = np.array([0.5, -0.3, 0.2, -2.0, 0.3, 1.5, 0.6])
    # Lowered to place the cube on the platform
    place_pose = np.array([0.5, -0.3, 0.2, -1.5, 0.3, 1.5, 0.6])

    # Gripper open / close targets (position)
    open_finger = np.array([0.04, 0.04])
    close_finger = np.array([0.0, 0.0])

    # Finite‑state machine for the pick‑and‑place sequence
    state = 0  # 0: to pre‑grasp, 1: to grasp, 2: close gripper,
               # 3: lift to pre‑grasp, 4: to pre‑place, 5: to place,
               # 6: open gripper, 7: to pre‑place, 8: done
    step_counter = 0
    hold_steps = 500   # number of simulation steps per phase (adjust if needed)

    while state != 8:
        if state == 0:
            franka.set_dofs_position(pre_grasp_pose, dofs_arm)
            franka.set_dofs_position(open_finger, dofs_finger)
            if step_counter > hold_steps:
                state = 1
        elif state == 1:
            franka.set_dofs_position(grasp_pose, dofs_arm)
            franka.set_dofs_position(open_finger, dofs_finger)
            if step_counter > 2 * hold_steps:
                state = 2
        elif state == 2:
            franka.set_dofs_position(grasp_pose, dofs_arm)
            franka.set_dofs_position(close_finger, dofs_finger)
            if step_counter > 2 * hold_steps + 100:
                state = 3
        elif state == 3:  # lift with cube
            franka.set_dofs_position(pre_grasp_pose, dofs_arm)
            franka.set_dofs_position(close_finger, dofs_finger)
            if step_counter > 3 * hold_steps + 100:
                state = 4
        elif state == 4:  # move over the platform
            franka.set_dofs_position(pre_place_pose, dofs_arm)
            franka.set_dofs_position(close_finger, dofs_finger)
            if step_counter > 4 * hold_steps + 100:
                state = 5
        elif state == 5:  # lower onto the platform
            franka.set_dofs_position(place_pose, dofs_arm)
            franka.set_dofs_position(close_finger, dofs_finger)
            if step_counter > 5 * hold_steps + 100:
                state = 6
        elif state == 6:  # release
            franka.set_dofs_position(place_pose, dofs_arm)
            franka.set_dofs_position(open_finger, dofs_finger)
            if step_counter > 5 * hold_steps + 200:
                state = 7
        elif state == 7:  # retract gripper
            franka.set_dofs_position(pre_place_pose, dofs_arm)
            franka.set_dofs_position(open_finger, dofs_finger)
            if step_counter > 6 * hold_steps + 200:
                state = 8

        scene.step()
        step_counter += 1

    # Keep the viewer open briefly after the operation
    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
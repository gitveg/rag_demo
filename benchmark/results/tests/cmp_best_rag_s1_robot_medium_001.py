import numpy as np
import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.5, 0.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
    ),
    rigid_options=gs.options.RigidOptions(
        dt=0.01,
    ),
    show_viewer=True,
)

plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

# Control only the 7 arm joints (exclude the 2 finger joints)
arm_dofs_idx = [0, 1, 2, 3, 4, 5, 6]
ee_link_idx = franka.get_link_index("left_finger")

# Target position in front of the robot (world coordinates)
target_pos = np.array([0.5, 0.0, 0.2])

kp = 10.0  # proportional gain
dt = scene.dt  # simulation timestep

for _ in range(500):
    # Get current end-effector position
    ee_pose = franka.get_link_pose(ee_link_idx)
    if hasattr(ee_pose, "cpu"):
        ee_pose = ee_pose.cpu().numpy()
    ee_pos = ee_pose[:3, 3]

    # Compute Jacobian transpose IK
    jac = franka.get_jacobian(ee_link_idx)
    if hasattr(jac, "cpu"):
        jac = jac.cpu().numpy()
    v = jac.T @ (target_pos - ee_pos) * kp

    # Update desired joint positions
    cur_q = franka.get_dofs_control(arm_dofs_idx)
    if hasattr(cur_q, "cpu"):
        cur_q = cur_q.cpu().numpy()
    target_q = cur_q + v * dt

    # Command the robot
    franka.set_dofs_position(arm_dofs_idx, target_q)
    scene.step()
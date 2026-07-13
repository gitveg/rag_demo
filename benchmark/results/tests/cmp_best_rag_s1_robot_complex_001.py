import numpy as np
import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3, -1, 1.5),
        camera_lookat=(0.5, 0.0, 0.2),
        camera_fov=30,
        max_FPS=60,
    ),
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    show_viewer=True,
)

# Add a plane (table)
plane = scene.add_entity(gs.morphs.Plane())

# Add a small rigid box on the table
box = scene.add_entity(
    gs.morphs.Box(
        pos=(0.5, 0.0, 0.015),   # half height of 0.03 box
        size=(0.03, 0.03, 0.03),
    )
)

# Load Franka Panda arm with gripper
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

# Get the end-effector link and DOF count
hand_link = franka.get_link("panda_hand")
n_dofs = franka.n_dofs
gripper_dof_idx = n_dofs - 1      # last DOF is the gripper joint (7 for 7+1 robot)

# Desired end-effector orientation (fingers pointing down)
ee_quat = np.array([0, 1, 0, 0])

# --- Pick up sequence ---
# 1. Move arm to pre-grasp pose above the box
target_pos = np.array([0.5, 0.0, 0.15])
arm_qpos = franka.inverse_kinematics(link=hand_link, pos=target_pos, quat=ee_quat)
franka.set_dofs_position(np.append(arm_qpos, 0.04))   # gripper open
for _ in range(100):
    scene.step()

# 2. Move down to grasp height
target_pos = np.array([0.5, 0.0, 0.05])
arm_qpos = franka.inverse_kinematics(link=hand_link, pos=target_pos, quat=ee_quat)
franka.set_dofs_position(np.append(arm_qpos, 0.04))
for _ in range(100):
    scene.step()

# 3. Close the gripper using force control
forces = np.zeros(n_dofs)
forces[gripper_dof_idx] = 5.0
franka.control_dofs_force(forces)
for _ in range(100):
    scene.step()

# Read the closed gripper position and use it for the remaining motion
closed_gripper_pos = franka.get_dofs_position()[gripper_dof_idx]

# 4. Lift the box
target_pos = np.array([0.5, 0.0, 0.3])
arm_qpos = franka.inverse_kinematics(link=hand_link, pos=target_pos, quat=ee_quat)
franka.set_dofs_position(np.append(arm_qpos, closed_gripper_pos))
for _ in range(100):
    scene.step()

# --- Place at a new location ---
# 5. Move to the destination above the table
target_pos = np.array([0.3, 0.3, 0.3])
arm_qpos = franka.inverse_kinematics(link=hand_link, pos=target_pos, quat=ee_quat)
franka.set_dofs_position(np.append(arm_qpos, closed_gripper_pos))
for _ in range(100):
    scene.step()

# 6. Lower the box onto the table
target_pos = np.array([0.3, 0.3, 0.05])
arm_qpos = franka.inverse_kinematics(link=hand_link, pos=target_pos, quat=ee_quat)
franka.set_dofs_position(np.append(arm_qpos, closed_gripper_pos))
for _ in range(100):
    scene.step()

# 7. Open the gripper to release
forces[gripper_dof_idx] = -5.0
franka.control_dofs_force(forces)
for _ in range(100):
    scene.step()

# 8. Retract the arm upwards
target_pos = np.array([0.3, 0.3, 0.3])
# Keep gripper open; use previously set position control (if any) or just let it stay open
# We'll simply open by setting the gripper joint to 0.04
arm_qpos = franka.inverse_kinematics(link=hand_link, pos=target_pos, quat=ee_quat)
franka.set_dofs_position(np.append(arm_qpos, 0.04))
for _ in range(100):
    scene.step()

# Run a few additional steps to let the scene settle
for _ in range(200):
    scene.step()
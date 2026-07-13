import genesis as gs
import numpy as np

gs.init()

scene = gs.Scene(
    show_viewer=True,
    show_FPS=True,
)

# Ground plane
plane = scene.add_entity(gs.morphs.Plane())

# Table (rigid box)
table = scene.add_entity(
    gs.morphs.Box(pos=(0.6, 0.0, 0.375), size=(0.8, 0.8, 0.05)),
    is_rigid=True,
)

# Small box to be picked up (rigid)
box = scene.add_entity(
    gs.morphs.Box(pos=(0.6, 0.0, 0.42), size=(0.04, 0.04, 0.04)),
    is_rigid=True,
)

# Load Franka Panda arm with gripper
robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

# Arm DOFs (7 revolute joints) and gripper DOFs (2 prismatic fingers)
arm_dofs = 7
gripper_dofs = 2
arm_indices = list(range(arm_dofs))
gripper_indices = list(range(arm_dofs, arm_dofs + gripper_dofs))

# End-effector link (gripper base / hand)
ee_link = robot.get_link("panda_hand")

# Define pick and place positions (world frame)
pick_above = np.array([0.6, 0.0, 0.55])    # above the box
pick_at    = np.array([0.6, 0.0, 0.44])    # grasping height
place_above = np.array([0.3, -0.2, 0.55])  # above target
place_at    = np.array([0.3, -0.2, 0.44])  # place height

open_gripper  = np.array([0.04, 0.04])
close_gripper = np.array([0.005, 0.005])

# Simulation / control loop
for step in range(600):
    if step < 80:
        # Phase 1: move above the box, gripper open
        q = robot.inverse_kinematics(link=ee_link, pos=pick_above)
        robot.set_dofs_position(q[:arm_dofs], arm_indices)
        robot.set_dofs_position(open_gripper, gripper_indices)
    elif step < 150:
        # Phase 2: lower to grasp
        q = robot.inverse_kinematics(link=ee_link, pos=pick_at)
        robot.set_dofs_position(q[:arm_dofs], arm_indices)
        robot.set_dofs_position(open_gripper, gripper_indices)
    elif step < 200:
        # Phase 3: close gripper
        q = robot.inverse_kinematics(link=ee_link, pos=pick_at)
        robot.set_dofs_position(q[:arm_dofs], arm_indices)
        robot.set_dofs_position(close_gripper, gripper_indices)
    elif step < 280:
        # Phase 4: lift object
        q = robot.inverse_kinematics(link=ee_link, pos=pick_above)
        robot.set_dofs_position(q[:arm_dofs], arm_indices)
        robot.set_dofs_position(close_gripper, gripper_indices)
    elif step < 400:
        # Phase 5: move above target location
        q = robot.inverse_kinematics(link=ee_link, pos=place_above)
        robot.set_dofs_position(q[:arm_dofs], arm_indices)
        robot.set_dofs_position(close_gripper, gripper_indices)
    elif step < 470:
        # Phase 6: lower to place
        q = robot.inverse_kinematics(link=ee_link, pos=place_at)
        robot.set_dofs_position(q[:arm_dofs], arm_indices)
        robot.set_dofs_position(close_gripper, gripper_indices)
    else:
        # Phase 7: open gripper to release
        q = robot.inverse_kinematics(link=ee_link, pos=place_at)
        robot.set_dofs_position(q[:arm_dofs], arm_indices)
        robot.set_dofs_position(open_gripper, gripper_indices)

    scene.step()
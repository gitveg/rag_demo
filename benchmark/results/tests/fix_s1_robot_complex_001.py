import numpy as np
import genesis as gs

# Initialize
gs.init(backend=gs.gpu)

# Create scene with viewer and simulator settings
scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3, -1, 1.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
        max_FPS=60,
    ),
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    show_viewer=True,
)

# Add a tabletop (a flat box)
table = scene.add_entity(
    gs.morphs.Box(pos=(0.5, 0.0, 0.02), size=(0.8, 0.8, 0.05), fixed=True),
)

# Add a small box on the table (pick target)
box = scene.add_entity(
    gs.morphs.Box(
        pos=(0.5, 0.0, 0.05),  # sits on top of the table
        size=(0.04, 0.04, 0.04),
        fixed=False,
    ),
    material=gs.materials.Rigid(rho=500.0),
)

# Load Franka Panda arm with gripper
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

# Build the scene (all entities must be added before this call)
scene.build()

# Identify the end‑effector link (hand) for IK targets
# In the MJCF file this body is typically named 'panda_hand'
ee_link = franka.get_link('panda_hand')

# Number of actuated joints (arm + fingers)
n_arm_joints = 7  # 7 DoF arm
n_fingers = 2     # two finger joints (gripper_grasping side)
total_joints = franka.n_qs

# PD control gains for the arm
kp = 200.0
kv = 20.0
franka.set_joint_kp(kp, joint_idxs=np.arange(n_arm_joints))
franka.set_joint_kv(kv, joint_idxs=np.arange(n_arm_joints))

# Gripper control gains (fingers separately)
finger_kp = 100.0
finger_kv = 10.0
finger_idxs = np.arange(n_arm_joints, total_joints)
franka.set_joint_kp(finger_kp, joint_idxs=finger_idxs)
franka.set_joint_kv(finger_kv, joint_idxs=finger_idxs)

# ---- Motion planning: pick and place waypoints ----
# Cartesian poses (position, quaternion [w,x,y,z])
# Above the object, pointing downward
pick_above_pos = np.array([0.5, 0.0, 0.2])
pick_above_quat = np.array([1, 0, 0, 0])  # identity orientation (gripper pointing forward)

# At the object (lower to grasp)
pick_grasp_pos = np.array([0.5, 0.0, 0.08])
pick_grasp_quat = np.array([1, 0, 0, 0])

# Above the object again (lift)
place_above_pos = np.array([0.7, 0.3, 0.2])  # new location
place_above_quat = np.array([1, 0, 0, 0])

# At the destination (lower to place)
place_drop_pos = np.array([0.7, 0.3, 0.08])
place_drop_quat = np.array([1, 0, 0, 0])

# Open/close gripper joint positions
open_fingers = np.array([0.04, 0.04])   # fully open (max)
close_fingers = np.array([0.0, 0.0])    # fully closed

def move_arm_to_pose(pos, quat, steps=100):
    """Use IK to reach a target pose and execute via PD joint control."""
    q_target = gs.utils.ik(ee_link, pos, quat)
    if q_target is None:  # IK failure fallback
        return
    # Send the arm part of the solution
    franka.set_joint_position(q_target[:n_arm_joints], joint_idxs=np.arange(n_arm_joints))
    for _ in range(steps):
        scene.step()

def set_gripper(targets, steps=50):
    """Close or open the gripper."""
    franka.set_joint_position(targets, joint_idxs=finger_idxs)
    for _ in range(steps):
        scene.step()

# ---- Execute the pick‑and‑place motion ----
# 1. Move above the object
move_arm_to_pose(pick_above_pos, pick_above_quat, steps=150)

# 2. Open gripper first
set_gripper(open_fingers, steps=50)

# 3. Descend to grasp
move_arm_to_pose(pick_grasp_pos, pick_grasp_quat, steps=100)

# 4. Close gripper
set_gripper(close_fingers, steps=80)

# 5. Lift object
move_arm_to_pose(pick_above_pos, pick_above_quat, steps=100)

# 6. Move to above the destination
move_arm_to_pose(place_above_pos, place_above_quat, steps=150)

# 7. Lower to drop position
move_arm_to_pose(place_drop_pos, place_drop_quat, steps=100)

# 8. Open gripper to release
set_gripper(open_fingers, steps=80)

# 9. Retract upward
move_arm_to_pose(place_above_pos, place_above_quat, steps=100)

print("Pick‑and‑place sequence completed. Keeping viewer open. Press 'Esc' in viewer to exit.")
# Keep the simulation running so the viewer stays open
while True:
    scene.step()
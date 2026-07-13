import numpy as np
import genesis as gs

# Initialize
gs.init()

# Create scene
scene = gs.Scene()

# Add entities
plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))

# Build scene
scene.build()

# Configure PD gains for all 9 DOFs (7 arm + 2 gripper)
kp = np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 200, 200], dtype=np.float32)
kv = np.array([450, 450, 350, 350, 200, 200, 200, 20, 20], dtype=np.float32)
franka.set_dofs_kp(kp)
franka.set_dofs_kv(kv)

# Get end-effector link
ee_link = franka.get_link("hand")

# Desired end-effector position
ee_pos = np.array([0.3, 0.2, 0.4], dtype=np.float32)
ee_quat = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)  # fixed orientation

# Solve inverse kinematics for target joint positions
target_qpos = franka.inverse_kinematics(
    link=ee_link,
    pos=ee_pos,
    quat=ee_quat,
)

# Simulation loop – drive the arm to the target
for _ in range(1000):
    franka.control_dofs_position(target_qpos)
    scene.step()
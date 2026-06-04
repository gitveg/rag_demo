import genesis as gs
import numpy as np

gs.init(backend=gs.cpu)

scene = gs.Scene()

# Add a ground plane
plane = scene.add_entity(gs.morphs.Plane())

# Add the Franka Panda arm from MJCF
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml")
)

scene.build()

# Get the end‑effector link
ee_link = franka.get_link("panda_hand")

# Desired end‑effector position in world frame (in front of the robot)
target_pos = np.array([0.5, 0.0, 0.5])

# Compute inverse kinematics to obtain joint positions
qpos = franka.inverse_kinematics(
    link=ee_link,
    pos=target_pos,
    quat=None,         # keep current orientation
)

# Command the robot to the computed joint configuration
franka.set_dofs_position(qpos)

# Run simulation to let the robot settle
for _ in range(200):
    scene.step()
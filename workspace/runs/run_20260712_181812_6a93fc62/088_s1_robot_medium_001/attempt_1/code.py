import genesis as gs
import numpy as np

gs.init(backend=gs.cpu)

scene = gs.Scene()

# Add a ground plane for reference (optional)
plane = scene.add_entity(
    gs.morphs.Plane(),
)

# Load the Franka Panda robot arm from MJCF
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

# Get initial joint configuration
q0 = franka.get_dofs_position()

# Define a target joint configuration that moves the end-effector forward
# (approximate values for a reaching pose in front of the robot)
target_q = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785])

# Smooth interpolation over 500 steps
num_steps = 500
for i in range(num_steps):
    t = i / num_steps
    q_des = q0 + (target_q - q0) * t
    franka.set_dofs_position(q_des)   # command joint positions
    scene.step()
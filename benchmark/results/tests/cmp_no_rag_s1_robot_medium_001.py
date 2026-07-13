import genesis as gs
import numpy as np

gs.init()

scene = gs.Scene(
    show_viewer=True,
)

robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

# Get initial joint positions and modify to make the arm reach forward
current_q = robot.get_dofs_position()
# Adjust a few joints (shoulder lift and elbow) for a forward‑reaching pose
current_q[1] = -0.5   # shoulder lift down
current_q[3] = -1.2   # elbow bend
robot.set_dofs_position(current_q)

# Run the simulation to let the arm settle at the target
for _ in range(1000):
    scene.step()
import genesis as gs
import numpy as np

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(
    gs.morphs.Plane(),
)
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml", requires_jac_and_IK=True),
)

scene.build()

# Target end-effector position
target_pos = np.array([0.3, 0.2, 0.4])

# Get initial joint positions
qpos = franka.get_qpos().copy()

# Identify end-effector link (hand)
link_hand = franka.get_link_idx('panda_hand')   # typical name, adapt if needed

# Inverse kinematics using damped least squares
max_iters = 500
damp = 0.01
error_threshold = 0.001
lr = 0.5

for _ in range(max_iters):
    franka.set_qpos(qpos)
    pos, _ = franka.get_link_pose(link_hand)   # position and quaternion
    error = target_pos - pos
    if np.linalg.norm(error) < error_threshold:
        break
    J = franka.get_jacobian(link_hand)[:3, :]  # position Jacobian (3 × dof)
    # Damped least squares: Δq = J^T (J J^T + λ I)^{-1} e
    JJT = J @ J.T + damp * np.eye(3)
    delta_q = J.T @ np.linalg.solve(JJT, error)
    qpos = qpos + lr * delta_q

# Set the converged joint positions
franka.set_qpos(qpos)

# Run simulation to visualize the robot in the target pose
for i in range(1000):
    scene.step()
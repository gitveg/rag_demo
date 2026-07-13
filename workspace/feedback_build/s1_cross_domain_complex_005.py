import genesis as gs
import numpy as np

gs.init(backend=gs.cpu)

scene = gs.Scene()

# Ground plane
plane = scene.add_entity(gs.morphs.Plane())

# Bumpy terrain (small patch)
terrain = scene.add_entity(
    gs.morphs.Terrain(subterrain_types=['random_uniform_terrain'], n_subterrains=(1,1)),
    pos=(1.0, 0.0, 0.0),
)

# Franka robotic arm
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

# Soft, deformable elastic cube
cube = scene.add_entity(
    gs.morphs.Box(pos=(0.5, 0.2, 0.5), size=(0.05, 0.05, 0.05)),
    material=gs.materials.PBD.Elastic(),
)

scene.build()

# Joint information (simplified: assuming 9 DOFs: 7 arm + 2 fingers)
num_dofs = franka.n_dofs
gripper_dofs = [num_dofs - 2, num_dofs - 1]  # finger joints

# Initial positions (used later for interpolation)
initial_dof_pos = franka.get_dofs_position()

# Target closed finger position (within limits)
close_value = 0.04  # arbitrary small positive value for prismatic finger

# Simulation loop
for step in range(3000):
    if step < 500:
        # Let everything settle, no control
        franka.set_dofs_position(initial_dof_pos)
    elif step < 800:
        # Gradually close gripper
        alpha = (step - 500) / 300.0
        target_q = initial_dof_pos.copy()
        target_q[gripper_dofs] = close_value
        franka.set_dofs_position(initial_dof_pos + alpha * (target_q - initial_dof_pos))
    elif step < 2000:
        # Move arm to a new location (raise and shift right)
        base_target = np.array([0.0, -0.5, 0.0, -1.5, 0.0, 1.0, 0.5])
        alpha = (step - 800) / 1200.0
        current_q = franka.get_dofs_position()
        target_q = current_q.copy()
        for i in range(7):
            target_q[i] = initial_dof_pos[i] + alpha * (base_target[i] - initial_dof_pos[i])
        # Keep fingers closed
        target_q[gripper_dofs] = close_value
        franka.set_dofs_position(target_q)
    else:
        # Hold final pose
        final_q = initial_dof_pos.copy()
        for i in range(7):
            final_q[i] = base_target[i]
        final_q[gripper_dofs] = close_value
        franka.set_dofs_position(final_q)

    scene.step()
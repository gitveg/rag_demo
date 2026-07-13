import numpy as np
import genesis as gs

gs.init()

scene = gs.Scene(show_viewer=True)

plane = scene.add_entity(gs.morphs.Plane())
robot = scene.add_entity(
    gs.morphs.URDF(
        file="urdf/go2/urdf/go2.urdf",
        pos=(0, 0, 0.4),
    )
)

scene.build()

# Get DOF indices for front legs
fl_joints = ["FL_hip_joint", "FL_thigh_joint", "FL_calf_joint"]
fr_joints = ["FR_hip_joint", "FR_thigh_joint", "FR_calf_joint"]

fl_dofs = [robot.get_joint(name).dof_idx_local for name in fl_joints]
fr_dofs = [robot.get_joint(name).dof_idx_local for name in fr_joints]

# Get default joint positions
default_pos = robot.get_dofs_position()

for i in range(1000):
    target_pos = default_pos.clone()

    # Alternate lifting front legs every 200 steps
    if (i // 200) % 2 == 0:
        # Lift front left leg
        target_pos[fl_dofs[0]] += 0.3
        target_pos[fl_dofs[1]] -= 0.6
        target_pos[fl_dofs[2]] += 1.0
    else:
        # Lift front right leg
        target_pos[fr_dofs[0]] -= 0.3
        target_pos[fr_dofs[1]] -= 0.6
        target_pos[fr_dofs[2]] += 1.0

    robot.control_dofs_position(target_pos)
    scene.step()
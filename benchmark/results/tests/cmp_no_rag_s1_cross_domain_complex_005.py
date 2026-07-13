import genesis as gs
import numpy as np

gs.init(backend=gs.gpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        gravity=(0, 0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3, -3, 2.5),
        camera_lookat=(0.2, 0.2, 0.4),
    ),
    show_viewer=True,
)

# Ground plane
ground = scene.add_entity(
    morph=gs.morphs.Plane(pos=(0, 0, 0)),
    material=gs.materials.Rigid(),
)

# Bumpy terrain: scatter random small rigid boxes
np.random.seed(42)
for _ in range(40):
    x = np.random.uniform(-2.5, 2.5)
    y = np.random.uniform(-2.5, 2.5)
    h = np.random.uniform(0.01, 0.12)
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(x, y, h / 2),
            size=(0.12, 0.12, h),
        ),
        material=gs.materials.Rigid(),
    )

# Soft deformable elastic cube (FEM)
soft_cube = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.5, 0.4, 0.2),
        size=(0.07, 0.07, 0.07),
    ),
    material=gs.materials.FEM.Elastic(
        E=5e4,
        nu=0.35,
        rho=1200,
    ),
)

# Franka Emika Panda robot arm
robot = scene.add_entity(
    morph=gs.morphs.URDF(
        file="franka_emika_panda/panda.urdf",
        pos=(0, 0, 0.03),
        fixed=True,
    ),
)

scene.build()

# Identify arm and gripper joints
dof_names = robot.dof_names
arm_dofs = [name for name in dof_names if "finger" not in name]
gripper_dofs = [name for name in dof_names if "finger" in name]

# Pick-and-place trajectory
target_pos = np.array([0.5, 0.4, 0.2])  # cube position

# Phase 1: Move above the cube
for _ in range(150):
    robot.control_dofs_position(
        target_pos[:3].tolist() + [0.04] * len(gripper_dofs),
        arm_dofs + gripper_dofs,
    )
    scene.step()

# Phase 2: Lower to grasp
for _ in range(100):
    robot.control_dofs_position(
        (target_pos[:3] + np.array([0, 0, -0.08])).tolist() + [0.0] * len(gripper_dofs),
        arm_dofs + gripper_dofs,
    )
    scene.step()

# Phase 3: Close gripper
for _ in range(80):
    robot.control_dofs_position(
        (target_pos[:3] + np.array([0, 0, -0.08])).tolist() + [0.01] * len(gripper_dofs),
        arm_dofs + gripper_dofs,
    )
    scene.step()

# Phase 4: Lift cube
for _ in range(120):
    robot.control_dofs_position(
        (target_pos[:3] + np.array([0, 0, 0.1])).tolist() + [0.01] * len(gripper_dofs),
        arm_dofs + gripper_dofs,
    )
    scene.step()

# Phase 5: Move to new location
new_pos = np.array([-0.3, -0.2, 0.3])
for _ in range(200):
    robot.control_dofs_position(
        new_pos.tolist() + [0.01] * len(gripper_dofs),
        arm_dofs + gripper_dofs,
    )
    scene.step()

# Phase 6: Lower to place
for _ in range(100):
    robot.control_dofs_position(
        (new_pos + np.array([0, 0, -0.12])).tolist() + [0.01] * len(gripper_dofs),
        arm_dofs + gripper_dofs,
    )
    scene.step()

# Phase 7: Open gripper to release
for _ in range(80):
    robot.control_dofs_position(
        (new_pos + np.array([0, 0, -0.12])).tolist() + [0.04] * len(gripper_dofs),
        arm_dofs + gripper_dofs,
    )
    scene.step()

# Phase 8: Retract arm
for _ in range(120):
    robot.control_dofs_position(
        (new_pos + np.array([0, 0, 0.15])).tolist() + [0.04] * len(gripper_dofs),
        arm_dofs + gripper_dofs,
    )
    scene.step()

# Let simulation settle
for _ in range(200):
    scene.step()

scene.viewer.stop()
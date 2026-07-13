import numpy as np
import genesis as gs

########################## init ##########################
gs.init()

########################## create a scene ##########################
scene = gs.Scene(
    show_viewer=True,
    rigid_options=gs.options.RigidOptions(
        dt=0.01,
        constraint_solver=gs.constraint_solver.Newton,
    ),
)

########################## entities ##########################
plane = scene.add_entity(gs.morphs.Plane())
robot = scene.add_entity(
    gs.morphs.URDF(
        file="urdf/go2/urdf/go2.urdf",
        pos=(0.0, 0.0, 0.4),
    ),
)

########################## build ##########################
scene.build()

# Print DOF info for debugging
print("DOF names:", robot.dof_names)
print("Number of DOFs:", robot.n_dofs)

# Set PD gains for position control on all joints
kp = np.full(robot.n_dofs, 100.0)
kv = np.full(robot.n_dofs, 20.0)
robot.set_dofs_kp(kp)
robot.set_dofs_kv(kv)

# Identify front leg joint indices by name prefix
dof_names = list(robot.dof_names)
fl_indices = [i for i, name in enumerate(dof_names) if name.startswith("FL_")]
fr_indices = [i for i, name in enumerate(dof_names) if name.startswith("FR_")]

print("Front-left joints:", [dof_names[i] for i in fl_indices])
print("Front-right joints:", [dof_names[i] for i in fr_indices])

# Let the robot settle into its default stance
for _ in range(100):
    scene.step()

# Capture default stance positions
dofs_default = robot.get_dofs_position().copy()

# Build target configurations for lifted front legs
dofs_fl_lift = dofs_default.copy()
dofs_fr_lift = dofs_default.copy()

# Lift front-left leg: rotate hip forward, bend knee
for idx in fl_indices:
    name = dof_names[idx].lower()
    if "hip" in name:
        dofs_fl_lift[idx] += 0.4
    elif "thigh" in name:
        dofs_fl_lift[idx] += 0.2
    elif "calf" in name:
        dofs_fl_lift[idx] -= 0.8

# Lift front-right leg symmetrically
for idx in fr_indices:
    name = dof_names[idx].lower()
    if "hip" in name:
        dofs_fr_lift[idx] += 0.4
    elif "thigh" in name:
        dofs_fr_lift[idx] += 0.2
    elif "calf" in name:
        dofs_fr_lift[idx] -= 0.8

########################## simulation loop ##########################
for step in range(2000):
    phase = (step // 200) % 4

    if phase == 0:
        robot.control_dofs_position(dofs_default)
    elif phase == 1:
        robot.control_dofs_position(dofs_fl_lift)
    elif phase == 2:
        robot.control_dofs_position(dofs_default)
    elif phase == 3:
        robot.control_dofs_position(dofs_fr_lift)

    scene.step()
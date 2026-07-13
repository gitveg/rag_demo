import genesis as gs

gs.init()

scene = gs.Scene(
    show_viewer=True,
)

# ground
plane = scene.add_entity(gs.morphs.Plane())

# load Go2 robot
robot = scene.add_entity(
    gs.morphs.URDF(file="urdf/go2/urdf/go2.urdf"),
    pos=(0, 0, 0.5),
)

scene.build()

# get joint names and indices for front legs
joint_names = robot.joint_names

fl_hip_idx   = joint_names.index("FL_hip")
fl_thigh_idx = joint_names.index("FL_thigh")
fl_calf_idx  = joint_names.index("FL_calf")
fr_hip_idx   = joint_names.index("FR_hip")
fr_thigh_idx = joint_names.index("FR_thigh")
fr_calf_idx  = joint_names.index("FR_calf")

# capture the robot's initial joint configuration (default stance from URDF)
n_joints = robot.n_joints
initial_positions = [robot.get_joint_position(i) for i in range(n_joints)]

# hold initial stance for a short settling period
for _ in range(200):
    robot.control_joints(pos=initial_positions)
    scene.step()

# target angles for lifting a front leg
lift_hip_angle   = 0.5
lift_thigh_angle = -0.8
calf_angle       = 0.0

# simulation loop (alternate lifting front legs every 200 steps)
for step in range(1000):
    targets = initial_positions.copy()

    if (step // 200) % 2 == 0:
        # lift left front leg
        targets[fl_hip_idx]   = lift_hip_angle
        targets[fl_thigh_idx] = lift_thigh_angle
        targets[fl_calf_idx]  = calf_angle
        # keep right front leg in initial stance
        targets[fr_hip_idx]   = initial_positions[fr_hip_idx]
        targets[fr_thigh_idx] = initial_positions[fr_thigh_idx]
        targets[fr_calf_idx]  = initial_positions[fr_calf_idx]
    else:
        # lift right front leg
        targets[fr_hip_idx]   = lift_hip_angle
        targets[fr_thigh_idx] = lift_thigh_angle
        targets[fr_calf_idx]  = calf_angle
        targets[fl_hip_idx]   = initial_positions[fl_hip_idx]
        targets[fl_thigh_idx] = initial_positions[fl_thigh_idx]
        targets[fl_calf_idx]  = initial_positions[fl_calf_idx]

    # rear leg joints stay at their initial standing values (untouched)
    robot.control_joints(pos=targets)
    scene.step()
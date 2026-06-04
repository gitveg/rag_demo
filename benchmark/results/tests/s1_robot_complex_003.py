"""
User Query: Load a Unitree Go2 quadruped robot (use gs.morphs.URDF(file="urdf/go2/urdf/go2.urdf")) and command it to lift its front legs one at a time while keeping the rear legs grounded.
task_id: s1_robot_complex_003
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.5, -2.5, 1.6),
        camera_lookat=(0.0, 0.0, 0.45),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(friction=1.5),
    surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8, 1.0)),
)

robot = scene.add_entity(
    gs.morphs.URDF(file="urdf/go2/urdf/go2.urdf", pos=(0.0, 0.0, 0.35)),
)

scene.build()

dofs = robot.n_dofs
print("Go2 dofs:", dofs)
for i in range(dofs):
    try:
        print(i, robot.get_dof_name(i))
    except Exception:
        pass

# Typical Go2 leg joint ordering in the Genesis/URDF model:
# FR: 0,1,2   FL: 3,4,5   RR: 6,7,8   RL: 9,10,11
# Each leg: [hip_abduction, hip_pitch, knee]
FR = [0, 1, 2]
FL = [3, 4, 5]
RR = [6, 7, 8]
RL = [9, 10, 11]

stand = [0.0] * dofs

# Rear legs grounded and stable
for idxs in (RR, RL):
    stand[idxs[0]] = 0.0
    stand[idxs[1]] = 0.8
    stand[idxs[2]] = -1.5

# Front legs normal standing pose
for idxs in (FR, FL):
    stand[idxs[0]] = 0.0
    stand[idxs[1]] = 0.8
    stand[idxs[2]] = -1.5

# Poses for lifting front-right and front-left legs
lift_fr = stand[:]
lift_fr[FR[1]] = 0.25
lift_fr[FR[2]] = -0.7
lift_fr[FL[1]] = 0.95
lift_fr[FL[2]] = -1.7

lift_fl = stand[:]
lift_fl[FL[1]] = 0.25
lift_fl[FL[2]] = -0.7
lift_fl[FR[1]] = 0.95
lift_fl[FR[2]] = -1.7

# Stronger rear-leg support during single-front-leg lifting
for pose in (lift_fr, lift_fl):
    pose[RR[1]] = 0.9
    pose[RR[2]] = -1.7
    pose[RL[1]] = 0.9
    pose[RL[2]] = -1.7

robot.set_dofs_kp([80.0] * dofs)
robot.set_dofs_kv([8.0] * dofs)
robot.set_dofs_force_range([-120.0] * dofs, [120.0] * dofs)
robot.control_dofs_position(stand)

def blend_pose(a, b, alpha):
    return [(1.0 - alpha) * x + alpha * y for x, y in zip(a, b)]

# Settle into standing posture
for _ in range(200):
    robot.control_dofs_position(stand)
    scene.step()

# Alternate lifting front legs one at a time
phases = [
    (stand, 80),
    (lift_fr, 120),
    (stand, 80),
    (lift_fl, 120),
    (stand, 80),
    (lift_fr, 120),
    (stand, 80),
    (lift_fl, 120),
    (stand, 80),
]

current = stand[:]
transition_steps = 40

for target, hold_steps in phases:
    start = current[:]
    for i in range(transition_steps):
        alpha = (i + 1) / transition_steps
        cmd = blend_pose(start, target, alpha)
        robot.control_dofs_position(cmd)
        scene.step()
    current = target[:]
    for _ in range(hold_steps):
        robot.control_dofs_position(current)
        scene.step()

print("Finished front-leg alternating lift motion.")
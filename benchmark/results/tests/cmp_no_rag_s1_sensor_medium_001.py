import genesis as gs
import numpy as np

gs.init()

scene = gs.Scene(show_viewer=True)

# Load Franka Panda robot
robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

# Attach IMU sensor to end-effector (panda_hand link)
imu = robot.add_sensor(
    gs.sensors.IMU,
    link='panda_hand',
)

# Build the scene
scene.build()

# Get joint names and find the first joint for motion
joint_names = robot.dof_names
target_joint = 'panda_joint1'
target_idx = joint_names.index(target_joint)

# PD control parameters
Kp = 100.0
Kd = 10.0

# Simulation loop
for i in range(500):
    # Current joint states
    q = robot.get_dofs_position()
    dq = robot.get_dofs_velocity()

    # Sinusoidal target for the first joint
    q_des = q.copy()
    q_des[target_idx] = 0.5 * np.pi * np.sin(i * 0.02)

    # PD torque control
    torque = Kp * (q_des - q) - Kd * dq
    robot.set_dofs_force(torque)

    # Read IMU data
    data = imu.get_data()
    print(f"Step {i}: acc = {data['acc']}, gyro = {data['gyro']}")

    scene.step()

# Cleanup
if scene.viewer:
    scene.viewer.stop()
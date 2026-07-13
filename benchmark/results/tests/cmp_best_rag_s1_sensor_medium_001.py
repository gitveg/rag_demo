import genesis as gs
import numpy as np

gs.init()

scene = gs.Scene(show_viewer=False)

plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

# attach IMU to end‑effector link (assumed name: "panda_hand")
imu = scene.add_sensor(
    gs.options.sensors.IMU(
        entity=franka,
        link="panda_hand",
    )
)

scene.build()

steps = 500
acc_data = np.zeros((steps, 3))
gyro_data = np.zeros((steps, 3))

for i in range(steps):
    t = i * 0.01
    target = np.array([
        0.0,
        0.3 * np.sin(t),
        0.0,
        -0.5,
        0.0,
        -0.3 * np.sin(t + 1.0),
        0.0
    ])
    # use PD control to drive joints
    franka.control_dofs_position(target, kp=100, kd=10)
    scene.step()
    acc_data[i] = imu.acc
    gyro_data[i] = imu.gyro

print("IMU data recorded. Accelerations (first 5):")
print(acc_data[:5])
print("Angular velocities (first 5):")
print(gyro_data[:5])
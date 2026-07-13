import genesis as gs
import numpy as np

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))

# Use the last link as the end-effector (typically the hand)
end_effector = franka.links[-1]

imu = scene.add_sensor(
    gs.sensors.IMU(
        entity_idx=franka.idx,
        link_idx_local=end_effector.idx_local,
    )
)

scene.build()

num_dofs = franka.n_dofs

acc_history = []
gyro_history = []

for step in range(1000):
    # Move the arm: sinusoidal motion on all joints
    targets = [0.5 * np.sin(step * 0.1 + i) for i in range(num_dofs)]
    franka.set_qpos(np.array(targets))

    scene.step()

    acc_history.append(imu.acc.copy())
    gyro_history.append(imu.gyro.copy())

print("Recorded", len(acc_history), "IMU readings.")
# Optionally print the last reading
print("Last acc:", acc_history[-1])
print("Last gyro:", gyro_history[-1])
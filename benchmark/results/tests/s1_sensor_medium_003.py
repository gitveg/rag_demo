"""
User Query: Equip a rigid body with an IMU sensor and record its linear acceleration as it falls and hits a platform.
task_id: s1_sensor_medium_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.005),
    renderer=gs.options.renderers.Rasterizer(),
)

ground = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8, 1.0)),
)

platform = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 0.5), size=(1.2, 1.2, 0.2)),
    material=gs.materials.Rigid(rho=500.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

falling_body = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 2.0), size=(0.2, 0.2, 0.2)),
    material=gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Aluminium(color=(0.9, 0.9, 0.9, 1.0)),
)

imu_opts = gs.sensors.IMU(
    entity_idx=falling_body.idx,
    link_idx_local=0,
    pos_offset=(0.0, 0.0, 0.0),
    acc_noise=0.0,
    gyro_noise=0.0,
)
imu = scene.add_sensor(imu_opts)

scene.build()

acc_log = []
time_log = []

num_steps = 600
dt = 0.005

for i in range(num_steps):
    scene.step()
    data = imu.read()
    acc_log.append(data.lin_acc)
    time_log.append((i + 1) * dt)

print("time_s, acc_x, acc_y, acc_z")
for t, acc in zip(time_log, acc_log):
    print(f"{t:.4f}, {acc[0]:.6f}, {acc[1]:.6f}, {acc[2]:.6f}")
"""
User Query: Build a scene with a rotating rigid box on the ground. Mount a Lidar sensor on a fixed pole pointing at the box. Run the simulation and capture the point cloud data as the box rotates.
task_id: s1_sensor_complex_001
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

ground = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(friction=1.0),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

box = scene.add_entity(
    gs.morphs.Box(pos=(2.0, 0.0, 0.5), size=(0.6, 0.4, 1.0)),
    material=gs.materials.Rigid(rho=200.0, friction=0.8),
    surface=gs.surfaces.Default(color=(0.8, 0.2, 0.2, 1.0)),
)

pole = scene.add_entity(
    gs.morphs.Cylinder(pos=(0.0, 0.0, 1.0), radius=0.05, height=2.0),
    material=gs.materials.Rigid(rho=500.0, friction=0.9),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

pattern = gs.sensors.SphericalPattern(
    fov=(120.0, 30.0),
    n_points=(240, 32),
)

lidar_opts = gs.sensors.Lidar(
    pattern=pattern,
    entity_idx=pole.idx,
    link_idx_local=0,
    pos_offset=(0.0, 0.0, 0.9),
)

lidar = scene.add_sensor(lidar_opts)

scene.build()

if hasattr(box, "set_pos"):
    box.set_pos((2.0, 0.0, 0.5))
if hasattr(box, "set_quat"):
    box.set_quat((1.0, 0.0, 0.0, 0.0))
if hasattr(box, "set_vel"):
    box.set_vel((0.0, 0.0, 0.0))
if hasattr(box, "set_ang_vel"):
    box.set_ang_vel((0.0, 0.0, 0.0))

num_steps = 300
yaw_rate = 0.03

all_point_clouds = []
all_distances = []

for step in range(num_steps):
    yaw = yaw_rate * step
    half_yaw = 0.5 * yaw
    quat = (
        math.cos(half_yaw),
        0.0,
        0.0,
        math.sin(half_yaw),
    )

    if hasattr(box, "set_pos"):
        box.set_pos((2.0, 0.0, 0.5))
    if hasattr(box, "set_quat"):
        box.set_quat(quat)
    if hasattr(box, "set_vel"):
        box.set_vel((0.0, 0.0, 0.0))
    if hasattr(box, "set_ang_vel"):
        box.set_ang_vel((0.0, 0.0, 0.0))

    scene.step()

    lidar_data = lidar.read()
    all_point_clouds.append(lidar_data.points)
    all_distances.append(lidar_data.distances)

    if step % 50 == 0:
        print(f"step={step}, num_points={lidar_data.points.shape[0]}")

print(f"Captured {len(all_point_clouds)} lidar frames.")
print(f"Last frame point cloud shape: {all_point_clouds[-1].shape}")
print(f"Last frame distance shape: {all_distances[-1].shape}")
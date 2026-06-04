"""
User Query: Attach a depth sensor to a moving cube and visualize the measured distance to the ground.
task_id: s1_sensor_simple_002
"""

import genesis as gs
import numpy as np

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

ground = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

cube = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 1.0), size=(0.3, 0.3, 0.3)),
    material=gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Default(color=(0.2, 0.5, 0.9, 1.0)),
)

cam_pattern = gs.sensors.DepthCameraPattern(res=(160, 120), fov_horizontal=60.0)
depth_opts = gs.sensors.DepthCamera(
    pattern=cam_pattern,
    entity_idx=cube.idx,
    link_idx_local=0,
    pos_offset=(0.0, 0.0, 0.0),
)
depth_sensor = scene.add_sensor(depth_opts)

scene.build()

num_steps = 600
amplitude = 0.6
base_height = 1.2
freq = 0.8

print("step,time,cube_z,center_distance_to_ground")

for i in range(num_steps):
    t = i * 0.01
    target_z = base_height + amplitude * np.sin(2.0 * np.pi * freq * t)
    cube.set_pos((0.0, 0.0, target_z))

    scene.step()

    data = depth_sensor.read()
    distances = data.distances
    h, w = distances.shape
    center_distance = float(distances[h // 2, w // 2])

    cube_z = float(cube.get_pos()[2])
    print(f"{i},{t:.2f},{cube_z:.4f},{center_distance:.4f}")
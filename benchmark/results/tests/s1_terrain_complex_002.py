"""
User Query: Create a large outdoor environment with mountainous terrain, scattered rocks, and rough paths. Simulate an off-road vehicle driving across the terrain while reacting realistically to bumps and slopes.
task_id: s1_terrain_complex_002
"""

import math
import random
import numpy as np
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(18.0, -18.0, 10.0),
        camera_lookat=(6.0, 0.0, 1.5),
        camera_fov=50,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

terrain = scene.add_entity(
    gs.morphs.Terrain(
        pos=(0.0, 0.0, 0.0),
        n_subterrains=(3, 3),
        subterrain_size=(12.0, 12.0),
        horizontal_scale=0.25,
        vertical_scale=0.01,
        subterrain_types=[
            ["fractal_terrain", "wave_terrain", "fractal_terrain"],
            ["sloped_terrain", "flat_terrain", "sloped_terrain"],
            ["fractal_terrain", "wave_terrain", "fractal_terrain"],
        ],
    ),
    surface=gs.surfaces.Rough(color=(0.42, 0.36, 0.24, 1.0)),
)

random.seed(7)

for _ in range(80):
    x = random.uniform(-14.0, 14.0)
    y = random.uniform(-14.0, 14.0)
    radius = random.uniform(0.15, 0.5)
    scene.add_entity(
        gs.morphs.Sphere(
            pos=(x, y, radius * 0.9 + 0.1),
            radius=radius,
        ),
        material=gs.materials.Rigid(
            rho=500.0,
            friction=1.4,
            coup_friction=0.1,
            coup_restitution=0.0,
        ),
        surface=gs.surfaces.Iron(color=(0.45, 0.47, 0.5, 1.0)),
    )

path_points = [(-12.0, -8.0), (-8.0, -5.0), (-3.0, -2.0), (2.0, 1.0), (7.0, 4.0), (12.0, 7.0)]
for i in range(len(path_points) - 1):
    x0, y0 = path_points[i]
    x1, y1 = path_points[i + 1]
    seg_len = math.hypot(x1 - x0, y1 - y0)
    yaw = math.atan2(y1 - y0, x1 - x0)
    scene.add_entity(
        gs.morphs.Box(
            pos=((x0 + x1) * 0.5, (y0 + y1) * 0.5, 0.03),
            size=(seg_len, 1.6, 0.06),
        ),
        material=gs.materials.Rigid(
            rho=250.0,
            friction=1.8,
            coup_friction=0.1,
            coup_restitution=0.0,
        ),
        surface=gs.surfaces.Rough(color=(0.33, 0.27, 0.18, 1.0)),
    )

vehicle_body = scene.add_entity(
    gs.morphs.Box(
        pos=(-13.0, -8.5, 1.2),
        size=(1.8, 1.0, 0.45),
    ),
    material=gs.materials.Rigid(
        rho=220.0,
        friction=1.2,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Default(color=(0.8, 0.15, 0.1, 1.0)),
)

wheel_offsets = [
    (0.65, 0.55, 0.75),
    (0.65, -0.55, 0.75),
    (-0.65, 0.55, 0.75),
    (-0.65, -0.55, 0.75),
]
wheels = []
for ox, oy, oz in wheel_offsets:
    wheel = scene.add_entity(
        gs.morphs.Cylinder(
            pos=(-13.0 + ox, -8.5 + oy, oz),
            radius=0.28,
            height=0.22,
        ),
        material=gs.materials.Rigid(
            rho=300.0,
            friction=2.5,
            coup_friction=0.1,
            coup_restitution=0.0,
        ),
        surface=gs.surfaces.Rough(color=(0.08, 0.08, 0.08, 1.0)),
    )
    wheels.append(wheel)

cam = scene.add_camera(
    res=(1280, 720),
    pos=(20.0, -20.0, 12.0),
    lookat=(0.0, 0.0, 1.0),
    fov=45,
)

scene.build()

target_speed = 2.2
steer_amplitude = 0.45
steps = 1800

for step in range(steps):
    t = step * 0.01

    vx = target_speed
    vy = 0.35 * math.sin(0.18 * t) + 0.15 * math.sin(0.53 * t)
    vz = 0.0

    if hasattr(vehicle_body, "set_vel"):
        vehicle_body.set_vel((vx, vy, vz))
    elif hasattr(vehicle_body, "set_velocity"):
        vehicle_body.set_velocity((vx, vy, vz))

    yaw = 0.15 + steer_amplitude * math.sin(0.12 * t)
    if hasattr(vehicle_body, "set_ang_vel"):
        vehicle_body.set_ang_vel((0.08 * math.sin(0.8 * t), 0.05 * math.cos(0.7 * t), yaw))
    elif hasattr(vehicle_body, "set_angular_velocity"):
        vehicle_body.set_angular_velocity((0.08 * math.sin(0.8 * t), 0.05 * math.cos(0.7 * t), yaw))

    wheel_spin = -8.0 - 2.0 * math.sin(0.5 * t)
    for i, wheel in enumerate(wheels):
        roll_rate = 0.1 * math.sin(t * 2.0 + i)
        pitch_rate = 0.06 * math.cos(t * 1.7 + i * 0.5)
        if hasattr(wheel, "set_ang_vel"):
            wheel.set_ang_vel((wheel_spin, pitch_rate, roll_rate))
        elif hasattr(wheel, "set_angular_velocity"):
            wheel.set_angular_velocity((wheel_spin, pitch_rate, roll_rate))

    if step % 6 == 0:
        body_pos = vehicle_body.get_pos()
        cam_pos = (
            body_pos[0] - 7.5,
            body_pos[1] - 7.5,
            body_pos[2] + 4.5,
        )
        cam_look = (
            body_pos[0] + 3.0,
            body_pos[1] + 1.5,
            body_pos[2] + 0.8,
        )
        if hasattr(cam, "set_pose"):
            cam.set_pose(pos=cam_pos, lookat=cam_look)

    scene.step()
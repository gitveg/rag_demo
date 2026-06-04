"""
User Query: Build an urban obstacle course with buildings and moving barriers. Simulate a drone autonomously navigating through the environment while avoiding collisions and maintaining stable flight.
task_id: s1_drone_complex_002
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(12.0, -12.0, 8.0),
        camera_lookat=(8.0, 0.0, 2.0),
        camera_fov=50,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

ground = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Rough(color=(0.18, 0.18, 0.18, 1.0)),
)

building_material = gs.materials.Rigid(rho=500.0, friction=0.9, coup_friction=0.1, coup_restitution=0.0)
barrier_material = gs.materials.Rigid(rho=300.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0)

buildings = []
building_specs = [
    ((2.0, -3.5, 1.5), (1.8, 1.8, 3.0), (0.45, 0.45, 0.50, 1.0)),
    ((2.0,  3.5, 1.8), (1.8, 1.8, 3.6), (0.42, 0.44, 0.50, 1.0)),
    ((5.0, -2.0, 2.1), (2.0, 2.2, 4.2), (0.50, 0.48, 0.46, 1.0)),
    ((5.2,  2.8, 1.4), (1.6, 1.6, 2.8), (0.40, 0.42, 0.48, 1.0)),
    ((8.5, -3.2, 2.4), (2.2, 1.8, 4.8), (0.48, 0.46, 0.44, 1.0)),
    ((8.3,  3.0, 2.0), (2.0, 2.0, 4.0), (0.44, 0.46, 0.50, 1.0)),
    ((11.5, -1.5, 2.7), (2.0, 2.4, 5.4), (0.52, 0.50, 0.48, 1.0)),
    ((11.8,  2.6, 1.7), (1.8, 1.8, 3.4), (0.43, 0.45, 0.47, 1.0)),
    ((14.5, -3.5, 2.2), (2.2, 2.0, 4.4), (0.47, 0.49, 0.52, 1.0)),
    ((14.0,  3.8, 2.6), (2.4, 2.0, 5.2), (0.49, 0.47, 0.45, 1.0)),
]
for pos, size, color in building_specs:
    buildings.append(
        scene.add_entity(
            gs.morphs.Box(pos=pos, size=size),
            material=building_material,
            surface=gs.surfaces.Rough(color=color),
        )
    )

corridor_posts = []
post_specs = [
    ((3.6, 0.0, 1.0), (0.35, 3.4, 2.0)),
    ((6.7, 0.0, 1.15), (0.35, 3.0, 2.3)),
    ((9.8, 0.0, 1.05), (0.35, 3.6, 2.1)),
    ((13.0, 0.0, 1.2), (0.35, 3.2, 2.4)),
]
for pos, size in post_specs:
    corridor_posts.append(
        scene.add_entity(
            gs.morphs.Box(pos=pos, size=size),
            material=building_material,
            surface=gs.surfaces.Iron(color=(0.35, 0.37, 0.40, 1.0)),
        )
    )

moving_barriers = []
moving_barrier_specs = [
    {
        "base": [4.0, 0.0, 1.6],
        "size": (0.25, 2.0, 0.25),
        "axis": "y",
        "amp": 1.2,
        "freq": 0.9,
        "phase": 0.0,
        "color": (0.85, 0.20, 0.20, 1.0),
    },
    {
        "base": [7.4, 0.0, 2.1],
        "size": (0.25, 2.2, 0.25),
        "axis": "z",
        "amp": 0.9,
        "freq": 1.1,
        "phase": 1.2,
        "color": (0.90, 0.55, 0.15, 1.0),
    },
    {
        "base": [10.6, 0.0, 1.7],
        "size": (0.25, 2.4, 0.25),
        "axis": "y",
        "amp": 1.0,
        "freq": 0.75,
        "phase": 2.3,
        "color": (0.90, 0.25, 0.25, 1.0),
    },
    {
        "base": [13.8, 0.0, 2.3],
        "size": (0.25, 2.0, 0.25),
        "axis": "z",
        "amp": 0.8,
        "freq": 1.0,
        "phase": 0.8,
        "color": (0.95, 0.60, 0.20, 1.0),
    },
]

for spec in moving_barrier_specs:
    ent = scene.add_entity(
        gs.morphs.Box(pos=tuple(spec["base"]), size=spec["size"]),
        material=barrier_material,
        surface=gs.surfaces.Emission(color=spec["color"]),
    )
    moving_barriers.append({"entity": ent, **spec})

drone = scene.add_entity(
    gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X", pos=(0.0, 0.0, 1.2)),
)

scene.build()

hover_rpm = 14468.429183500699
dt = 0.01
total_steps = 2200

waypoints = [
    (1.5, 0.0, 1.3),
    (3.0, -0.9, 1.5),
    (4.8, 0.9, 1.9),
    (6.5, -0.6, 1.7),
    (8.7, 0.8, 2.2),
    (10.8, -0.7, 1.8),
    (13.0, 0.7, 2.2),
    (15.5, 0.0, 1.8),
]

wp_idx = 0
prev_pos = drone.get_pos()
filtered_vel = [0.0, 0.0, 0.0]
last_target_y = 0.0
last_target_z = 1.2

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def vec_sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]

for step in range(total_steps):
    t = step * dt

    for spec in moving_barriers:
        pos = list(spec["base"])
        offset = spec["amp"] * math.sin(2.0 * math.pi * spec["freq"] * t + spec["phase"])
        if spec["axis"] == "y":
            pos[1] += offset
        else:
            pos[2] += offset
        spec["entity"].set_pos(tuple(pos))

    pos = drone.get_pos()
    vel_raw = (
        (pos[0] - prev_pos[0]) / dt,
        (pos[1] - prev_pos[1]) / dt,
        (pos[2] - prev_pos[2]) / dt,
    )
    filtered_vel[0] = 0.85 * filtered_vel[0] + 0.15 * vel_raw[0]
    filtered_vel[1] = 0.85 * filtered_vel[1] + 0.15 * vel_raw[1]
    filtered_vel[2] = 0.85 * filtered_vel[2] + 0.15 * vel_raw[2]
    prev_pos = pos

    if wp_idx < len(waypoints) - 1:
        dx = waypoints[wp_idx][0] - pos[0]
        dy = waypoints[wp_idx][1] - pos[1]
        dz = waypoints[wp_idx][2] - pos[2]
        if math.sqrt(dx * dx + dy * dy + dz * dz) < 0.7:
            wp_idx += 1

    target = waypoints[wp_idx]
    target_x, target_y, target_z = target

    rep_y = 0.0
    rep_z = 0.0

    for bpos, bsize, _ in building_specs:
        cx, cy, cz = bpos
        sx, sy, sz = bsize
        dx = pos[0] - cx
        dy = pos[1] - cy
        dz = pos[2] - cz

        safety_x = sx * 0.5 + 1.2
        safety_y = sy * 0.5 + 1.2
        safety_z = sz * 0.5 + 0.9

        if abs(dx) < safety_x:
            if abs(dy) < safety_y:
                sign_y = 1.0 if dy >= 0.0 else -1.0
                rep_y += sign_y * (safety_y - abs(dy)) * 0.9
            if abs(dz) < safety_z:
                sign_z = 1.0 if dz >= 0.0 else -1.0
                rep_z += sign_z * (safety_z - abs(dz)) * 0.7

    for post_pos, post_size in post_specs:
        cx, cy, cz = post_pos
        sx, sy, sz = post_size
        dx = pos[0] - cx
        dy = pos[1] - cy
        dz = pos[2] - cz
        if abs(dx) < sx * 0.5 + 1.0:
            if abs(dy) < sy * 0.5 + 0.8:
                sign_y = 1.0 if dy >= 0.0 else -1.0
                rep_y += sign_y * ((sy * 0.5 + 0.8) - abs(dy)) * 1.2
            if abs(dz) < sz * 0.5 + 0.7:
                sign_z = 1.0 if dz >= 0.0 else -1.0
                rep_z += sign_z * ((sz * 0.5 + 0.7) - abs(dz)) * 0.8

    for spec in moving_barriers:
        bpos = spec["entity"].get_pos()
        sx, sy, sz = spec["size"]
        rel = vec_sub(pos, bpos)
        if abs(rel[0]) < 1.4:
            margin_y = sy * 0.5 + 0.9
            margin_z = sz * 0.5 + 0.9
            if abs(rel[1]) < margin_y:
                sign_y = 1.0 if rel[1] >= 0.0 else -1.0
                rep_y += sign_y * (margin_y - abs(rel[1])) * 1.8
            if abs(rel[2]) < margin_z:
                sign_z = 1.0 if rel[2] >= 0.0 else -1.0
                rep_z += sign_z * (margin_z - abs(rel[2])) * 1.6

    target_y = clamp(target_y + rep_y, -2.6, 2.6)
    target_z = clamp(target_z + rep_z, 1.0, 3.0)

    target_y = 0.7 * last_target_y + 0.3 * target_y
    target_z = 0.7 * last_target_z + 0.3 * target_z
    last_target_y = target_y
    last_target_z = target_z

    err_x = target_x - pos[0]
    err_y = target_y - pos[1]
    err_z = target_z - pos[2]

    vx_cmd = clamp(1.2 * err_x - 0.35 * filtered_vel[0], -0.45, 0.45)
    vy_cmd = clamp(1.4 * err_y - 0.50 * filtered_vel[1], -0.35, 0.35)
    vz_cmd = clamp(1.8 * err_z - 0.60 * filtered_vel[2], -0.30, 0.30)

    thrust = 4200.0 * vz_cmd + 1200.0 * err_z
    pitch = clamp(2200.0 * vx_cmd, -1800.0, 1800.0)
    roll = clamp(-2400.0 * vy_cmd, -1800.0, 1800.0)

    yaw_centering = clamp(-120.0 * pos[1], -150.0, 150.0)
    yaw = yaw_centering

    m1 = hover_rpm + thrust - roll - pitch - yaw
    m2 = hover_rpm + thrust - roll + pitch + yaw
    m3 = hover_rpm + thrust + roll + pitch - yaw
    m4 = hover_rpm + thrust + roll - pitch - yaw

    rpms = [
        clamp(m1, 11000.0, 18500.0),
        clamp(m2, 11000.0, 18500.0),
        clamp(m3, 11000.0, 18500.0),
        clamp(m4, 11000.0, 18500.0),
    ]

    drone.set_propellels_rpm(rpms)
    scene.step()
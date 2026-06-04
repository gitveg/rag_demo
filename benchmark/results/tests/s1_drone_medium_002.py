"""
User Query: Create a Crazyflie 2.P drone (use gs.morphs.Drone(file="urdf/drones/cf2p.urdf", model="CF2P")) that takes off, flies through three floating checkpoints, and lands at a target position.
task_id: s1_drone_medium_002
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
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

checkpoint_positions = [
    (0.8, 0.0, 0.8),
    (1.6, 0.6, 1.0),
    (2.2, -0.4, 0.7),
]
checkpoint_radius = 0.12

for i, p in enumerate(checkpoint_positions):
    scene.add_entity(
        gs.morphs.Sphere(pos=p, radius=checkpoint_radius),
        material=gs.materials.Rigid(rho=50.0, friction=0.5),
        surface=gs.surfaces.Emission(
            color=(
                1.0 if i == 0 else 0.3,
                1.0 if i == 1 else 0.3,
                1.0 if i == 2 else 0.3,
                1.0,
            )
        ),
    )

landing_target = (2.8, 0.0, 0.18)
scene.add_entity(
    gs.morphs.Cylinder(pos=landing_target, radius=0.22, height=0.04),
    material=gs.materials.Rigid(rho=100.0, friction=1.2),
    surface=gs.surfaces.Gold(color=(1.0, 0.84, 0.0, 1.0)),
)

drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2p.urdf",
        model="CF2P",
        pos=(0.0, 0.0, 0.12),
    )
)

cam = scene.add_camera(
    pos=(4.2, -3.2, 2.4),
    lookat=(1.4, 0.0, 0.8),
    res=(1280, 720),
    fov=50,
)

scene.build()

hover_rpm = 14468.429183500699

waypoints = [
    (0.0, 0.0, 0.8),
    checkpoint_positions[0],
    checkpoint_positions[1],
    checkpoint_positions[2],
    (landing_target[0], landing_target[1], 0.55),
    landing_target,
]

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def dist3(a, b):
    return math.sqrt(
        (a[0] - b[0]) ** 2 +
        (a[1] - b[1]) ** 2 +
        (a[2] - b[2]) ** 2
    )

wp_idx = 0
arrive_hold_steps = 0
max_steps = 2200

for step in range(max_steps):
    pos = drone.get_pos()
    target = waypoints[wp_idx]

    ex = target[0] - pos[0]
    ey = target[1] - pos[1]
    ez = target[2] - pos[2]

    horiz_tol = 0.16 if wp_idx < len(waypoints) - 1 else 0.10
    vert_tol = 0.14 if wp_idx < len(waypoints) - 1 else 0.08

    if abs(ex) < horiz_tol and abs(ey) < horiz_tol and abs(ez) < vert_tol:
        arrive_hold_steps += 1
    else:
        arrive_hold_steps = 0

    if arrive_hold_steps > 12 and wp_idx < len(waypoints) - 1:
        wp_idx += 1
        arrive_hold_steps = 0
        target = waypoints[wp_idx]
        ex = target[0] - pos[0]
        ey = target[1] - pos[1]
        ez = target[2] - pos[2]

    thrust = clamp(ez * 5200.0, -2200.0, 2600.0)

    pitch = clamp(ex * 1800.0, -900.0, 900.0)
    roll = clamp(-ey * 1800.0, -900.0, 900.0)

    yaw = 0.0

    m1 = hover_rpm + thrust - roll - pitch - yaw
    m2 = hover_rpm + thrust - roll + pitch + yaw
    m3 = hover_rpm + thrust + roll + pitch - yaw
    m4 = hover_rpm + thrust + roll - pitch - yaw

    min_rpm = 8000.0
    max_rpm = 22000.0
    rpms = [
        clamp(m1, min_rpm, max_rpm),
        clamp(m2, min_rpm, max_rpm),
        clamp(m3, min_rpm, max_rpm),
        clamp(m4, min_rpm, max_rpm),
    ]

    if wp_idx == len(waypoints) - 1 and dist3(pos, landing_target) < 0.14 and pos[2] < 0.20:
        rpms = [hover_rpm - 1800.0] * 4

    drone.set_propellels_rpm(rpms)
    scene.step()

for _ in range(160):
    drone.set_propellels_rpm([hover_rpm - 2500.0] * 4)
    scene.step()
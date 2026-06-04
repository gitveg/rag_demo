"""
User Query: Command a Crazyflie 2.X drone (use gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X")) to fly in a horizontal circle with radius 2 meters while maintaining altitude.
task_id: s1_drone_medium_003
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Default(color=(0.7, 0.7, 0.7, 1.0)),
)

drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
        pos=(2.0, 0.0, 1.0),
    )
)

scene.build()

hover_rpm = 14468.429183500699
target_z = 1.0
radius = 2.0
omega = 0.4
center_x = 0.0
center_y = 0.0

kp_z = 2200.0
kd_z = 900.0

kp_xy = 180.0
kd_xy = 120.0

prev_ex = 0.0
prev_ey = 0.0
prev_ez = 0.0
dt = 0.01

steps = 3000
for i in range(steps):
    t = i * dt

    target_x = center_x + radius * math.cos(omega * t)
    target_y = center_y + radius * math.sin(omega * t)
    target_vx = -radius * omega * math.sin(omega * t)
    target_vy = radius * omega * math.cos(omega * t)

    pos = drone.get_pos()

    ex = target_x - pos[0]
    ey = target_y - pos[1]
    ez = target_z - pos[2]

    dex = (ex - prev_ex) / dt
    dey = (ey - prev_ey) / dt
    dez = (ez - prev_ez) / dt

    cmd_x = kp_xy * ex + kd_xy * (target_vx + dex)
    cmd_y = kp_xy * ey + kd_xy * (target_vy + dey)
    thrust = kp_z * ez + kd_z * dez

    pitch = max(-500.0, min(500.0, cmd_x))
    roll = max(-500.0, min(500.0, -cmd_y))
    yaw = 0.0
    thrust = max(-1500.0, min(1500.0, thrust))

    m1 = hover_rpm + thrust - roll - pitch - yaw
    m2 = hover_rpm + thrust - roll + pitch + yaw
    m3 = hover_rpm + thrust + roll + pitch - yaw
    m4 = hover_rpm + thrust + roll - pitch - yaw

    rpms = [
        max(0.0, m1),
        max(0.0, m2),
        max(0.0, m3),
        max(0.0, m4),
    ]

    drone.set_propellels_rpm(rpms)
    scene.step()

    prev_ex = ex
    prev_ey = ey
    prev_ez = ez
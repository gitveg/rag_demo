"""
User Query: Simulate a Crazyflie 2.X drone (use gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X")) flying a square path: move forward 3m, turn right, repeat four times, then land.
task_id: s1_drone_complex_001
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    renderer=gs.options.renderers.Rasterizer(),
)

plane = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(
        rho=200.0,
        friction=1.0,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8, 1.0)),
)

drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
        pos=(0.0, 0.0, 0.3),
    )
)

scene.build()

hover_rpm = 14468.429183500699

target_altitude = 1.0
dt_assumed = 0.01

kp_z = 3500.0
kd_z = 1200.0

kp_yaw = 1.8
kd_yaw = 0.35

forward_pitch_cmd = 220.0
turn_yaw_cmd = 260.0

square_side = 3.0
pos_tolerance = 0.12
yaw_tolerance = math.radians(6.0)

phase = "takeoff"
segment_index = 0
segment_start_pos = None
segment_target_yaw = 0.0

prev_z_error = 0.0
prev_yaw_error = 0.0

def wrap_angle(a):
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a

def get_yaw_from_quat(q):
    x, y, z, w = q
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)

max_steps = 5000

for step in range(max_steps):
    pos = drone.get_pos()
    quat = drone.get_quat()
    yaw = get_yaw_from_quat(quat)

    z_error = target_altitude - pos[2]
    z_error_rate = (z_error - prev_z_error) / dt_assumed
    thrust = kp_z * z_error + kd_z * z_error_rate
    prev_z_error = z_error

    pitch = 0.0
    roll = 0.0
    yaw_cmd = 0.0

    if phase == "takeoff":
        if abs(z_error) < 0.08 and pos[2] > 0.92:
            phase = "forward"
            segment_start_pos = tuple(pos)

    elif phase == "forward":
        if segment_start_pos is None:
            segment_start_pos = tuple(pos)

        dx = pos[0] - segment_start_pos[0]
        dy = pos[1] - segment_start_pos[1]
        distance = math.sqrt(dx * dx + dy * dy)

        pitch = forward_pitch_cmd

        yaw_error = wrap_angle(segment_target_yaw - yaw)
        yaw_error_rate = (yaw_error - prev_yaw_error) / dt_assumed
        yaw_cmd = kp_yaw * yaw_error + kd_yaw * yaw_error_rate

        if distance >= square_side - pos_tolerance:
            phase = "turn"
            segment_target_yaw = wrap_angle(segment_target_yaw - math.pi / 2.0)

    elif phase == "turn":
        yaw_error = wrap_angle(segment_target_yaw - yaw)
        yaw_error_rate = (yaw_error - prev_yaw_error) / dt_assumed
        yaw_cmd = kp_yaw * yaw_error + kd_yaw * yaw_error_rate

        yaw_cmd += -turn_yaw_cmd

        if abs(yaw_error) < yaw_tolerance:
            segment_index += 1
            if segment_index >= 4:
                phase = "land"
                target_altitude = 0.12
            else:
                phase = "forward"
                segment_start_pos = tuple(pos)

    elif phase == "land":
        yaw_error = wrap_angle(segment_target_yaw - yaw)
        yaw_error_rate = (yaw_error - prev_yaw_error) / dt_assumed
        yaw_cmd = kp_yaw * yaw_error + kd_yaw * yaw_error_rate

        if pos[2] < 0.08:
            drone.set_propellels_rpm([0.0, 0.0, 0.0, 0.0])
            break

    prev_yaw_error = wrap_angle(segment_target_yaw - yaw)

    m1 = hover_rpm + thrust - roll - pitch - yaw_cmd
    m2 = hover_rpm + thrust - roll + pitch + yaw_cmd
    m3 = hover_rpm + thrust + roll + pitch - yaw_cmd
    m4 = hover_rpm + thrust + roll - pitch - yaw_cmd

    rpms = [
        max(0.0, m1),
        max(0.0, m2),
        max(0.0, m3),
        max(0.0, m4),
    ]

    drone.set_propellels_rpm(rpms)
    scene.step()
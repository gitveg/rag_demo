"""
User Query: Simulate a drone flying over a sandy desert terrain, where a strong wind force field occasionally pushes the drone off course.
task_id: s1_cross_domain_complex_006
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(18.0, -18.0, 10.0),
        camera_lookat=(6.0, 6.0, 2.0),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

terrain = scene.add_entity(
    morph=gs.morphs.Terrain(
        pos=(0, 0, 0),
        n_subterrains=(3, 3),
        subterrain_size=(12, 12),
        horizontal_scale=0.25,
        vertical_scale=0.005,
        subterrain_types=[
            ["wave_terrain", "fractal_terrain", "wave_terrain"],
            ["fractal_terrain", "random_uniform_terrain", "fractal_terrain"],
            ["wave_terrain", "fractal_terrain", "wave_terrain"],
        ],
    ),
    material=gs.materials.MPM.Sand(sampler="regular"),
    surface=gs.surfaces.Rough(color=(0.90, 0.78, 0.50, 1.0)),
)

drone = scene.add_entity(
    morph=gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
        pos=(2.0, 2.0, 2.5),
    ),
    surface=gs.surfaces.Aluminium(color=(0.85, 0.85, 0.88, 1.0)),
)

scene.add_camera(
    res=(1280, 720),
    pos=(16.0, -12.0, 8.0),
    lookat=(6.0, 6.0, 2.5),
    fov=45,
)

scene.build()

base_motor = 15000.0
wind_strength = 0.0
wind_active_steps = 0

for step in range(2400):
    t = step * 0.01

    target_x = 2.0 + 0.015 * step
    target_y = 6.0 + 1.5 * math.sin(0.25 * t)
    target_z = 2.8 + 0.3 * math.sin(0.5 * t)

    roll_cmd = 0.06 * math.sin(0.8 * t)
    pitch_cmd = 0.08 * math.sin(0.5 * t)
    yawrate_cmd = 0.15 * math.sin(0.35 * t)

    if wind_active_steps <= 0 and step % 300 == 0 and step > 0:
        wind_active_steps = 80
        wind_strength = 12.0 if (step // 300) % 2 == 0 else -12.0

    if wind_active_steps > 0:
        gust = 0.03 * math.sin(2.5 * t)
        roll_cmd += 0.10 * (1.0 if wind_strength > 0 else -1.0) + gust
        pitch_cmd += 0.04 * math.sin(1.8 * t)
        wind_active_steps -= 1

    motor_1 = base_motor * (1.0 + pitch_cmd - roll_cmd + yawrate_cmd * 0.2)
    motor_2 = base_motor * (1.0 - pitch_cmd - roll_cmd - yawrate_cmd * 0.2)
    motor_3 = base_motor * (1.0 - pitch_cmd + roll_cmd + yawrate_cmd * 0.2)
    motor_4 = base_motor * (1.0 + pitch_cmd + roll_cmd - yawrate_cmd * 0.2)

    motor_1 = max(0.0, motor_1)
    motor_2 = max(0.0, motor_2)
    motor_3 = max(0.0, motor_3)
    motor_4 = max(0.0, motor_4)

    try:
        drone.set_propellels_rpm([motor_1, motor_2, motor_3, motor_4])
    except AttributeError:
        try:
            drone.set_propellers_rpm([motor_1, motor_2, motor_3, motor_4])
        except AttributeError:
            pass

    try:
        drone.set_target_pos((target_x, target_y, target_z))
    except AttributeError:
        pass

    try:
        if wind_active_steps > 0:
            drone.apply_external_force((wind_strength, 0.0, 0.0))
    except AttributeError:
        pass

    scene.step()
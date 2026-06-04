"""
User Query: Load a Crazyflie 2.X drone (use gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X")) flying over uneven terrain (gs.morphs.Terrain with fractal_terrain). Apply a turbulent wind force field that pushes the drone off course.
task_id: s1_cross_domain_complex_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

terrain = scene.add_entity(
    gs.morphs.Terrain(
        pos=(0.0, 0.0, 0.0),
        n_subterrains=(1, 1),
        subterrain_size=(12.0, 12.0),
        horizontal_scale=0.25,
        vertical_scale=0.005,
        subterrain_types="fractal_terrain",
    )
)

drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
        pos=(0.0, 0.0, 1.5),
    )
)

scene.add_force_field(
    gs.force_fields.Turbulence(
        strength=6.0,
        frequency=0.8,
    )
)

scene.build()

hover_rpm = 14468.429183500699
target_z = 1.5

for step in range(1000):
    current_z = drone.get_pos()[2]
    z_error = target_z - current_z
    thrust_adjust = z_error * 2500.0

    forward_drift = 200.0
    right_drift = -120.0
    yaw_bias = 40.0

    m1 = hover_rpm + thrust_adjust - right_drift - forward_drift - yaw_bias
    m2 = hover_rpm + thrust_adjust - right_drift + forward_drift + yaw_bias
    m3 = hover_rpm + thrust_adjust + right_drift + forward_drift - yaw_bias
    m4 = hover_rpm + thrust_adjust + right_drift - forward_drift - yaw_bias

    drone.set_propellels_rpm([m1, m2, m3, m4])
    scene.step()

    if step % 100 == 0:
        pos = drone.get_pos()
        print(f"step={step:04d}, drone_pos=({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
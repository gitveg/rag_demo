"""
User Query: Spawn a Crazyflie 2.X quadcopter drone (use gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X")) and make it hover steadily at 1 meter above the ground.
task_id: s1_drone_simple_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(friction=1.0),
    surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8, 1.0)),
)

drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
        pos=(0.0, 0.0, 0.5),
    )
)

scene.build()

hover_rpm = 14468.429183500699
target_z = 1.0
kp = 3500.0
kd = 1200.0
prev_error = target_z - 0.5
dt = 0.01

for _ in range(1000):
    current_z = drone.get_pos()[2]
    error = target_z - current_z
    error_rate = (error - prev_error) / dt

    rpm_cmd = hover_rpm + kp * error + kd * error_rate
    min_rpm = 0.0
    max_rpm = hover_rpm * 1.8
    rpm_cmd = max(min_rpm, min(max_rpm, rpm_cmd))

    drone.set_propellels_rpm([rpm_cmd, rpm_cmd, rpm_cmd, rpm_cmd])

    scene.step()
    prev_error = error
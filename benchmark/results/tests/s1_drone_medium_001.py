"""
User Query: Create a Crazyflie 2.X drone (use gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X")) that takes off from the ground, hovers at 2 meters for 3 seconds, then lands back down.
task_id: s1_drone_medium_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8, 1.0)),
)

drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
        pos=(0.0, 0.0, 0.05),
    )
)

scene.build()

hover_rpm = 14468.429183500699
dt = 0.01

target_hover_z = 2.0
hover_duration = 3.0

takeoff_kp = 3500.0
takeoff_kd = 1200.0

landing_kp = 3200.0
landing_kd = 1400.0

prev_z = drone.get_pos()[2]
hover_steps = int(hover_duration / dt)
hover_counter = 0
phase = "takeoff"

for step in range(2000):
    pos = drone.get_pos()
    z = pos[2]
    vz = (z - prev_z) / dt
    prev_z = z

    if phase == "takeoff":
        error = target_hover_z - z
        thrust_adjust = takeoff_kp * error - takeoff_kd * vz
        rpm = hover_rpm + thrust_adjust

        if abs(error) < 0.08 and abs(vz) < 0.15:
            phase = "hover"
            hover_counter = 0

    elif phase == "hover":
        error = target_hover_z - z
        thrust_adjust = takeoff_kp * error - takeoff_kd * vz
        rpm = hover_rpm + thrust_adjust
        hover_counter += 1

        if hover_counter >= hover_steps:
            phase = "landing"

    else:
        target_z = 0.08
        error = target_z - z
        thrust_adjust = landing_kp * error - landing_kd * vz
        rpm = hover_rpm + thrust_adjust

        if z <= 0.10 and abs(vz) < 0.12:
            rpm = 0.0

    rpm = max(0.0, min(25000.0, rpm))
    drone.set_propellels_rpm([rpm, rpm, rpm, rpm])

    scene.step()

    if phase == "landing" and z <= 0.10 and abs(vz) < 0.12:
        for _ in range(50):
            drone.set_propellels_rpm([0.0, 0.0, 0.0, 0.0])
            scene.step()
        break
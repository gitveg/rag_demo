"""
User Query: Spawn a Crazyflie 2.X drone (use gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X")) and make it take off to a height of 1.5 meters.
task_id: s1_drone_simple_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Default(color=(0.7, 0.7, 0.7, 1.0)),
)

drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
        pos=(0.0, 0.0, 0.2),
    )
)

scene.build()

hover_rpm = 14468.429183500699
target_z = 1.5
kp = 5000.0

for _ in range(600):
    current_z = drone.get_pos()[2]
    error = target_z - current_z
    adjusted = hover_rpm + kp * error
    adjusted = max(0.0, adjusted)

    drone.set_propellels_rpm([adjusted, adjusted, adjusted, adjusted])
    scene.step()

final_pos = drone.get_pos()
print("Final drone position:", final_pos)
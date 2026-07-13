import genesis as gs

gs.init(seed=0)

scene = gs.Scene(
    show_viewer=True,
)

# Ground plane for collision
plane = scene.add_entity(gs.morphs.Plane())

# Crazyflie 2.X drone at 1m altitude
drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
        pos=(0.0, 0.0, 1.0),
    ),
)

scene.build()

# Base hover RPM from reference drone control example
hover_rpm = 14475.8

for _ in range(2000):
    drone.set_rpms([hover_rpm] * 4)
    scene.step()
import genesis as gs
import numpy as np

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    show_viewer=True,
)

plane = scene.add_entity(gs.morphs.Plane())
drone = scene.add_entity(
    gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X")
)

scene.build()

radius = 2.0
altitude = 1.0
omega = 1.0
dt = 0.01

t = 0.0
for _ in range(500):
    x = radius * np.cos(omega * t)
    y = radius * np.sin(omega * t)
    z = altitude
    new_qpos = np.array([x, y, z, 1.0, 0.0, 0.0, 0.0])
    drone.set_qpos(new_qpos)
    scene.step()
    t += dt
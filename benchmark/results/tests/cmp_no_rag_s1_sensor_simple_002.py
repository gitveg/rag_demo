import genesis as gs
import matplotlib.pyplot as plt

gs.init()

scene = gs.Scene()

plane = scene.add_entity(gs.morphs.Plane())
cube = scene.add_entity(
    gs.morphs.Box(pos=(0, 0, 1), size=(0.2, 0.2, 0.2)),
)

sensor = scene.add_sensor(
    gs.sensors.RaySensor(
        parent=cube,
        offset=(0, 0, -0.1),
        direction=(0, 0, -1),
        max_dist=5.0,
    )
)

scene.build()

dists = []
for i in range(500):
    scene.step()
    dist = sensor.distance
    dists.append(dist)

plt.plot(dists)
plt.xlabel("Step")
plt.ylabel("Distance (m)")
plt.title("Depth sensor distance to ground")
plt.show()
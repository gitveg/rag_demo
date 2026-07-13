import genesis as gs
import numpy as np

gs.init(backend=gs.cpu)

scene = gs.Scene(
    dt=0.01,
    gravity=(0, 0, -9.81),
    show_viewer=False,
    show_FPS=False,
)

plane = scene.add_entity(
    gs.morphs.Plane(),
)

sphere = scene.add_entity(
    gs.morphs.Sphere(
        radius=0.5,
        pos=(0, 0, 2),
    ),
    material=gs.materials.Rigid(),
)

scene.build()

# Sphere mass: density (default 1000) * volume
volume = (4/3) * np.pi * (0.5 ** 3)
mass = 1000 * volume
g = 9.81
force_magnitude = mass * g

sphere.add_force(
    gs.forces.ConstantForce(
        direction=(0, 0, 1),
        magnitude=force_magnitude,
    )
)

for _ in range(1000):
    scene.step()

pos = sphere.get_pos()
print(f"Final sphere position: {pos}")
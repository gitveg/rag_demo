import genesis as gs
import math

gs.init()

scene = gs.Scene(
    gravity=(0, -9.8, 0),
    dt=0.01,
    substeps=2,
)

# Floor plane to catch the pooling water
scene.add_rigid_body(
    type='plane',
    pos=(0, 0, 0),
    normal=(0, 1, 0),
    fixed=True,
)

# Slanted surface: a thin box rotated around the Z-axis
scene.add_rigid_body(
    type='box',
    pos=(0.8, 0.6, 0),
    size=(2.0, 0.1, 1.0),
    euler=(0, 0, 0.45),  # ~25° tilt
    fixed=True,
)

# Create a small block of water particles above the slanted surface
num_particles = 800
positions = []
velocities = []
for i in range(8):
    for j in range(8):
        for k in range(8):
            x = (i - 4) * 0.04
            y = 1.8 + (j - 4) * 0.04
            z = (k - 4) * 0.04
            positions.append((x, y, z))
            velocities.append((0, -2.5, 0))

scene.add_fluid_particles(
    positions=positions,
    velocities=velocities,
    radius=0.02,
    color=(0.3, 0.6, 1.0),
)

scene.build()

# Simulate
for _ in range(600):
    scene.step()
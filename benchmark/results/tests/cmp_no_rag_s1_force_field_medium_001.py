import genesis as gs
import numpy as np

gs.init(backend=gs.gpu)

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(5, -5, 5),
        camera_lookat=(0, 0, 1),
    ),
    sim_options=gs.options.SimOptions(
        dt=0.01,
        gravity=(0, 0, -9.81),
    ),
)

# Ground plane
plane = scene.add_entity(gs.morphs.Plane())

# Sphere properties
radius = 0.3
density = 1000.0  # default rigid body density (kg/m^3)
volume = (4.0 / 3.0) * np.pi * radius**3
mass = volume * density
g = 9.81

# Three spheres dropped from different heights
sphere_left = scene.add_entity(
    gs.morphs.Sphere(pos=(-1.0, 0.0, 3.0), radius=radius),
    material=gs.materials.Rigid(),
)
sphere_middle = scene.add_entity(
    gs.morphs.Sphere(pos=(0.0, 0.0, 5.0), radius=radius),
    material=gs.materials.Rigid(),
)
sphere_right = scene.add_entity(
    gs.morphs.Sphere(pos=(1.0, 0.0, 4.0), radius=radius),
    material=gs.materials.Rigid(),
)

scene.build()

# Upward force exactly canceling gravity: F = m * g (in +z direction)
upward_force = np.array([0.0, 0.0, mass * g])

# Simulation loop
for i in range(500):
    # Apply strong upward force only to the middle sphere
    sphere_middle.add_force(upward_force)
    scene.step()
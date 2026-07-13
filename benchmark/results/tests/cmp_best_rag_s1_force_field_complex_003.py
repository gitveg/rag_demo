import numpy as np
import genesis as gs

gs.init()

scene = gs.Scene(
    rigid_options=gs.options.RigidOptions(
        gravity=(0, 0, 0),  # no global gravity, only the radial force
    ),
    show_viewer=True,
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(0, 0, 5),
        camera_lookat=(0, 0, 0),
    ),
)

# Place several rigid spheres around the center
n_spheres = 8
radius = 2.0
for i in range(n_spheres):
    angle = i * 2 * np.pi / n_spheres
    x = radius * np.cos(angle)
    y = radius * np.sin(angle)
    scene.add_entity(
        gs.options.morphs.Sphere(pos=(x, y, 0.5), radius=0.3),
        material=gs.materials.Rigid(),
    )

# Visual marker at the vacuum point
scene.draw_debug_sphere(pos=(0.0, 0.0, 0.0), radius=0.15, color=(1.0, 0.0, 0.0, 0.8))

# Add the central attractive radial force field
scene.add_force_field(
    force_field=gs.force_fields.RadialForce(
        center=(0.0, 0.0, 0.0),
        strength=100.0,  # magnitude; sign controls attraction vs repulsion
    )
)

scene.build()

# Simulate for 500 steps
for _ in range(500):
    scene.step()
import numpy as np
import genesis as gs

# Initialize Genesis
gs.init()

# Create the scene with SPH solver and visualization options
scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    sph_options=gs.options.SPHOptions(
        lower_bound=(-0.5, -0.5, 0.0),
        upper_bound=(0.5, 0.5, 3.0),
        particle_size=0.01,
    ),
    vis_options=gs.options.VisOptions(
        visualize_sph_boundary=True,
    ),
    show_viewer=True,
)

# Bowl: base plane at z=0
plane = scene.add_entity(gs.options.morphs.Plane())

# Bowl: cylindrical side walls (closed at bottom by the plane)
bowl_wall = scene.add_entity(
    gs.options.morphs.Cylinder(
        pos=(0.0, 0.0, 0.5),
        radius=0.5,
        height=1.0,
    )
)

# High-speed liquid stream: tall, tilted box filled with SPH liquid
# Tilted 30° around the y-axis to pour from an angle
tilt_angle = np.radians(30)
quat_tilt = (
    np.cos(tilt_angle / 2),  # w
    0.0,                     # x
    np.sin(tilt_angle / 2),  # y
    0.0                      # z
)

liquid_stream = scene.add_entity(
    gs.options.morphs.Box(
        pos=(0.3, 0.0, 2.0),           # high up and offset to hit bowl inner wall
        size=(0.1, 0.1, 1.0),          # thin tall column
        quat=quat_tilt,
    ),
    material=gs.materials.SPH.Liquid(),
)

# Build the scene (required before simulation)
scene.build()

# Run simulation
while True:
    scene.step()
import os
import genesis as gs

gs.init()

# Create scene with SPH liquid
scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    sph_options=gs.options.SPHOptions(
        lower_bound=(-0.5, -0.5, 0.0),
        upper_bound=(0.5, 0.5, 1),
        particle_size=0.01,
    ),
    vis_options=gs.options.VisOptions(
        visualize_sph_boundary=True,
    ),
    show_viewer=True,
)

# Bowl: bottom plane
scene.add_entity(
    morph=gs.options.morphs.Plane(
        pos=(0.0, 0.0, 0.0),
        euler=(0.0, 0.0, 0.0),
    ),
    material=gs.materials.Rigid(),
)

# Bowl walls: four side planes
# Left wall
scene.add_entity(
    morph=gs.options.morphs.Plane(
        pos=(-0.3, 0.0, 0.15),
        euler=(0.0, 0.0, 0.0),
    ),
    material=gs.materials.Rigid(),
)

# Right wall
scene.add_entity(
    morph=gs.options.morphs.Plane(
        pos=(0.3, 0.0, 0.15),
        euler=(0.0, 0.0, 0.0),
    ),
    material=gs.materials.Rigid(),
)

# Back wall
scene.add_entity(
    morph=gs.options.morphs.Plane(
        pos=(0.0, 0.3, 0.15),
        euler=(0.0, 0.0, 0.0),
    ),
    material=gs.materials.Rigid(),
)

# Front wall
scene.add_entity(
    morph=gs.options.morphs.Plane(
        pos=(0.0, -0.3, 0.15),
        euler=(0.0, 0.0, 0.0),
    ),
    material=gs.materials.Rigid(),
)

# Build the scene
scene.build()

# Run simulation
for i in range(1000):
    scene.step()
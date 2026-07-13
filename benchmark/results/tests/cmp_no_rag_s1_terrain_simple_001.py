import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(show_viewer=True)

# Add hilly terrain
terrain = scene.add_entity(
    gs.morphs.Terrain(
        subterrain_types="fractal_terrain",
        n_subterrains=(8, 8),
        subterrain_size=(10.0, 10.0),
        horizontal_scale=0.2,
        vertical_scale=2.0,
    ),
    pos=(0, 0, 0),
)

# Add a rigid sphere above the center of the terrain
sphere = scene.add_entity(
    gs.morphs.Sphere(radius=0.5),
    material=gs.materials.Rigid(),
    pos=(0, 3.0, 0),  # assumed above a peak
)

scene.build()

# Run the simulation for a few seconds to let the sphere roll down
for _ in range(1000):
    scene.step()
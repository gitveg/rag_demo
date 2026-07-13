import genesis as gs
import numpy as np

gs.init(backend=gs.cpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(10, -10, 8),
        camera_lookat=(0, 0, 0),
    ),
    show_viewer=True,
)

# Create two terrains side by side
fractal_terrain = scene.add_entity(
    gs.morphs.Terrain(
        terrain='fractal',       # fractal subtype
        size=(5.0, 5.0),
        pos=(-3.0, 0.0, 0.0),
    ),
)

random_terrain = scene.add_entity(
    gs.morphs.Terrain(
        terrain='random_uniform',# random_uniform subtype
        size=(5.0, 5.0),
        pos=(3.0, 0.0, 0.0),
    ),
)

# Drop cubes onto different parts of the terrains
cube_size = 0.15

# Cubes over the fractal terrain (x in [-5.5, -0.5], y in [-2.5, 2.5])
for _ in range(4):
    x = np.random.uniform(-5.0, -1.0)
    y = np.random.uniform(-2.0, 2.0)
    scene.add_entity(
        gs.morphs.Rigid(
            gs.morphs.Box(pos=(x, y, 2.0), size=(cube_size, cube_size, cube_size)),
            material=gs.materials.Rigid(),
        ),
    )

# Cubes over the random_uniform terrain (x in [0.5, 5.5], y in [-2.5, 2.5])
for _ in range(4):
    x = np.random.uniform(1.0, 5.0)
    y = np.random.uniform(-2.0, 2.0)
    scene.add_entity(
        gs.morphs.Rigid(
            gs.morphs.Box(pos=(x, y, 2.0), size=(cube_size, cube_size, cube_size)),
            material=gs.materials.Rigid(),
        ),
    )

# Run simulation to let cubes settle
for _ in range(1000):
    scene.step()
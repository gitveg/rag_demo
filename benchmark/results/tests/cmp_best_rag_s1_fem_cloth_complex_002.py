import numpy as np
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_fov=30,
        res=(1280, 720),
        max_FPS=60,
    ),
    show_viewer=True,
)

# Ground plane
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

# Heavy box acting as a table
table = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.4),
        size=(1.0, 1.0, 0.8),
    ),
    material=gs.materials.Rigid(rho=10000),
    surface=gs.surfaces.Default(),
)

# Tablecloth mesh (make sure meshes/cloth.obj is accessible)
cloth = scene.add_entity(
    morph=gs.morphs.Mesh(
        file="meshes/cloth.obj",
        pos=(0.0, 0.0, 0.85),
    ),
    material=gs.materials.PBD.Cloth(),
    surface=gs.surfaces.Default(),
)

# Several small cubes that will drop onto the cloth
num_cubes = 5
cube_size = 0.08
for _ in range(num_cubes):
    x = np.random.uniform(-0.3, 0.3)
    y = np.random.uniform(-0.3, 0.3)
    z = np.random.uniform(1.0, 1.5)
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(x, y, z),
            size=(cube_size, cube_size, cube_size),
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(),
    )

scene.build()

# Simulation loop
for _ in range(1000):
    scene.step()
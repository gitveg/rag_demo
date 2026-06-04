"""
User Query: A rigid sphere falls onto a soft elastic sheet stretched horizontally, causing the sheet to deform.
task_id: s1_cross_domain_medium_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.005),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, -3.0, 2.0),
        camera_lookat=(0.0, 0.0, 0.6),
        camera_fov=40,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(
        rho=200.0,
        friction=0.8,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

sheet = scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 0.8),
        size=(1.6, 1.6, 0.03),
    ),
    material=gs.materials.FEM.Elastic(
        rho=1000.0,
        E=8.0e4,
        nu=0.3,
        model="linear",
    ),
    surface=gs.surfaces.Default(color=(0.3, 0.6, 0.9, 1.0)),
)

ball = scene.add_entity(
    gs.morphs.Sphere(
        pos=(0.0, 0.0, 1.8),
        radius=0.18,
    ),
    material=gs.materials.Rigid(
        rho=500.0,
        friction=0.4,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

scene.build()

for _ in range(1000):
    scene.step()
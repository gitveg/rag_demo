"""
User Query: A piece of cloth falls and drapes over a box.
task_id: s1_fem_cloth_simple_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.5, -2.0, 1.8),
        camera_lookat=(0.0, 0.0, 0.6),
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

scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 0.25),
        size=(0.6, 0.6, 0.5),
    ),
    material=gs.materials.Rigid(
        rho=200.0,
        friction=0.7,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 1.0),
        size=(1.0, 1.0, 0.02),
    ),
    material=gs.materials.FEM.Cloth(
        rho=0.5,
        E=5e4,
        nu=0.49,
        thickness=0.001,
        model="stable_neohookean",
    ),
    surface=gs.surfaces.Default(color=(0.3, 0.5, 0.9, 1.0)),
)

scene.build()

for _ in range(600):
    scene.step()
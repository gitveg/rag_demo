"""
User Query: A soft elastic cube falls from the air and bounces off the ground.
task_id: s1_fem_elastic_simple_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.005),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.5, -2.5, 1.8),
        camera_lookat=(0.0, 0.0, 0.5),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.4),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(pos=(0.0, 0.0, 1.0), size=(0.4, 0.4, 0.4)),
    material=gs.materials.FEM.Elastic(
        density=1000,
        youngs_modulus=1e5,
        poissons_ratio=0.3,
    ),
    surface=gs.surfaces.Default(color=(0.3, 0.6, 1.0, 1.0)),
)

scene.build()

for _ in range(600):
    scene.step()
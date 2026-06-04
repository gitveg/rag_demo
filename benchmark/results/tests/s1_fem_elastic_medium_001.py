"""
User Query: Create a soft elastic cube sitting on a flat surface, then drop a rigid sphere onto it from above. The cube should visibly deform under the impact.
task_id: s1_fem_elastic_medium_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=10,
        gravity=(0, 0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.5, -2.5, 1.8),
        camera_lookat=(0.0, 0.0, 0.35),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.1),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.18),
        size=(0.35, 0.35, 0.35),
    ),
    material=gs.materials.FEM.Elastic(
        density=1000,
        youngs_modulus=8e4,
        poissons_ratio=0.35,
    ),
    surface=gs.surfaces.Default(color=(0.3, 0.7, 1.0, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(0.0, 0.0, 0.95),
        radius=0.12,
    ),
    material=gs.materials.Rigid(rho=2500, friction=0.5, restitution=0.05),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

scene.build()

for _ in range(800):
    scene.step()
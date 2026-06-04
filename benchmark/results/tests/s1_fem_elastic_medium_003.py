"""
User Query: Place three squishy elastic spheres of different sizes in a row. Let them drop simultaneously onto a flat surface to see them deform upon impact.
task_id: s1_fem_elastic_medium_003
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
        camera_pos=(4.0, -6.0, 3.0),
        camera_lookat=(0.0, 0.0, 0.8),
        camera_fov=40,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(
        rho=2000,
        friction=0.8,
        restitution=0.1,
    ),
    surface=gs.surfaces.Rough(color=(0.75, 0.75, 0.78, 1.0)),
)

elastic_material = gs.materials.FEM.Elastic(
    density=1000,
    youngs_modulus=8e4,
    poissons_ratio=0.35,
)

scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(-0.9, 0.0, 1.6),
        radius=0.22,
    ),
    material=elastic_material,
    surface=gs.surfaces.Default(color=(1.0, 0.4, 0.4, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(0.0, 0.0, 1.75),
        radius=0.30,
    ),
    material=elastic_material,
    surface=gs.surfaces.Default(color=(0.4, 1.0, 0.4, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(1.1, 0.0, 1.95),
        radius=0.38,
    ),
    material=elastic_material,
    surface=gs.surfaces.Default(color=(0.4, 0.6, 1.0, 1.0)),
)

scene.build()

for _ in range(900):
    scene.step()
"""
User Query: Load the Stanford Bunny mesh as a soft elastic body (use gs.morphs.Mesh(file="meshes/bunny.obj")). Rest it on a platform, then drop several rigid metal spheres onto it from different heights so the bunny compresses and recovers.
task_id: s1_fem_elastic_complex_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.005),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.8, -2.2, 1.8),
        camera_lookat=(0.0, 0.0, 0.45),
    ),
    renderer=gs.options.renderers.RayTracer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=2000, friction=0.9, restitution=0.1),
    surface=gs.surfaces.Rough(color=(0.45, 0.45, 0.48, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.12),
        size=(1.2, 1.2, 0.24),
    ),
    material=gs.materials.Rigid(rho=2500, friction=0.8, restitution=0.05),
    surface=gs.surfaces.Iron(color=(0.35, 0.36, 0.40, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Mesh(
        file="meshes/bunny.obj",
        pos=(0.0, 0.0, 0.42),
        scale=0.9,
    ),
    material=gs.materials.FEM.Elastic(
        density=1000,
        youngs_modulus=8e4,
        poissons_ratio=0.35,
    ),
    surface=gs.surfaces.Default(color=(0.88, 0.82, 0.72, 1.0)),
)

sphere_radius = 0.09
sphere_specs = [
    ((-0.18, -0.10, 1.25), (0.72, 0.74, 0.78, 1.0)),
    ((0.16, 0.08, 1.55), (0.78, 0.80, 0.84, 1.0)),
    ((0.00, -0.18, 1.85), (0.68, 0.70, 0.74, 1.0)),
    ((0.12, 0.18, 2.15), (0.82, 0.84, 0.88, 1.0)),
]

for pos, color in sphere_specs:
    scene.add_entity(
        morph=gs.morphs.Sphere(pos=pos, radius=sphere_radius),
        material=gs.materials.Rigid(rho=7800, friction=0.35, restitution=0.1),
        surface=gs.surfaces.Iron(color=color),
    )

scene.add_camera(
    pos=(2.6, -2.0, 1.6),
    lookat=(0.0, 0.0, 0.55),
    res=(1280, 720),
)

scene.build()

for _ in range(1500):
    scene.step()
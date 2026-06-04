"""
User Query: Generate a hilly terrain using gs.morphs.Terrain with subterrain_types="fractal_terrain" and proper parameters (n_subterrains, subterrain_size, horizontal_scale, vertical_scale). Place a rigid sphere at the top of a hill to roll down.
task_id: s1_terrain_simple_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    renderer=gs.options.renderers.Rasterizer(),
)

terrain = scene.add_entity(
    gs.morphs.Terrain(
        pos=(0.0, 0.0, 0.0),
        n_subterrains=(2, 2),
        subterrain_size=(6.0, 6.0),
        horizontal_scale=0.25,
        vertical_scale=0.005,
        subterrain_types="fractal_terrain",
    )
)

sphere = scene.add_entity(
    material=gs.materials.Rigid(
        rho=200.0,
        friction=0.4,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    morph=gs.morphs.Sphere(
        pos=(1.5, 1.5, 2.5),
        radius=0.25,
    ),
    surface=gs.surfaces.Rough(
        color=(0.9, 0.2, 0.2, 1.0),
    ),
)

scene.build()

for _ in range(1000):
    scene.step()
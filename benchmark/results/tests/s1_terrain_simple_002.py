"""
User Query: Generate a gently sloped terrain using gs.morphs.Terrain with subterrain_types="sloped_terrain". Place a rigid sphere on the slope and let it roll downhill.
task_id: s1_terrain_simple_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

terrain = scene.add_entity(
    gs.morphs.Terrain(
        pos=(0, 0, 0),
        n_subterrains=(1, 1),
        subterrain_size=(8.0, 8.0),
        horizontal_scale=0.25,
        vertical_scale=0.005,
        subterrain_types="sloped_terrain",
    )
)

sphere = scene.add_entity(
    morph=gs.morphs.Sphere(pos=(1.5, 0.0, 1.2), radius=0.25),
    material=gs.materials.Rigid(
        rho=200.0,
        friction=0.2,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

scene.build()

for _ in range(1000):
    scene.step()
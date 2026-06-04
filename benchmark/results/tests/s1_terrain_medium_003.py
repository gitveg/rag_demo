"""
User Query: Create a large terrain with rolling hills and valleys, and place a rigid box on one of the slopes to see it slide down.
task_id: s1_terrain_medium_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

terrain = scene.add_entity(
    gs.morphs.Terrain(
        pos=(0.0, 0.0, 0.0),
        n_subterrains=(2, 2),
        subterrain_size=(12.0, 12.0),
        horizontal_scale=0.25,
        vertical_scale=0.02,
        subterrain_types=[
            ["wave_terrain", "fractal_terrain"],
            ["sloped_terrain", "wave_terrain"],
        ],
    )
)

box = scene.add_entity(
    gs.morphs.Box(
        pos=(4.0, 4.0, 2.5),
        size=(0.8, 0.8, 0.8),
    ),
    material=gs.materials.Rigid(
        rho=200.0,
        friction=0.15,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Rough(color=(0.85, 0.25, 0.2, 1.0)),
)

camera = scene.add_camera(
    pos=(18.0, 18.0, 10.0),
    lookat=(4.0, 4.0, 1.5),
    res=(1280, 720),
)

scene.build()

for i in range(600):
    scene.step()
    if i % 60 == 0:
        p = box.get_pos()
        print(f"step={i:03d}, box_pos=({p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f})")
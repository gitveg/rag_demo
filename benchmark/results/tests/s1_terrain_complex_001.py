"""
User Query: Generate terrain using gs.morphs.Terrain with half "sloped_terrain" and half "stairs_terrain" in a 3x3 grid. Simulate a rigid box sliding down the steep side and a sphere rolling down the stair side simultaneously.
task_id: s1_terrain_complex_001
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
        n_subterrains=(3, 3),
        subterrain_size=(6.0, 6.0),
        horizontal_scale=0.25,
        vertical_scale=0.005,
        subterrain_types=[
            ["sloped_terrain", "sloped_terrain", "stairs_terrain"],
            ["sloped_terrain", "sloped_terrain", "stairs_terrain"],
            ["sloped_terrain", "stairs_terrain", "stairs_terrain"],
        ],
    )
)

box = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-6.0, -3.0, 2.0),
        size=(0.6, 0.6, 0.6),
    ),
    material=gs.materials.Rigid(
        rho=200.0,
        friction=0.08,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Iron(),
)

sphere = scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(6.0, 3.0, 2.0),
        radius=0.35,
    ),
    material=gs.materials.Rigid(
        rho=200.0,
        friction=0.6,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Gold(),
)

camera = scene.add_camera(
    pos=(18.0, 18.0, 12.0),
    lookat=(0.0, 0.0, 0.0),
    res=(1280, 720),
)

scene.build()

for step in range(1000):
    scene.step()
    if step % 100 == 0:
        box_pos = box.get_pos()
        sphere_pos = sphere.get_pos()
        print(f"step={step} box_pos={box_pos} sphere_pos={sphere_pos}")
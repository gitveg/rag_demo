"""
User Query: Create a bumpy terrain using gs.morphs.Terrain with subterrain_types including "random_uniform_terrain" and "wave_terrain" in a 3x3 grid. Drop three rigid spheres at different locations and watch them roll into the valleys.
task_id: s1_terrain_medium_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(12.0, 12.0, 8.0),
        camera_lookat=(0.0, 0.0, 0.0),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

terrain = scene.add_entity(
    gs.morphs.Terrain(
        pos=(0.0, 0.0, 0.0),
        n_subterrains=(3, 3),
        subterrain_size=(6.0, 6.0),
        horizontal_scale=0.25,
        vertical_scale=0.01,
        subterrain_types=[
            ["random_uniform_terrain", "wave_terrain", "random_uniform_terrain"],
            ["wave_terrain", "random_uniform_terrain", "wave_terrain"],
            ["random_uniform_terrain", "wave_terrain", "random_uniform_terrain"],
        ],
    )
)

sphere_material = gs.materials.Rigid(
    rho=200.0,
    friction=1.2,
    coup_friction=0.1,
    coup_restitution=0.0,
)

sphere_surface_1 = gs.surfaces.Default(color=(0.9, 0.2, 0.2, 1.0))
sphere_surface_2 = gs.surfaces.Default(color=(0.2, 0.9, 0.2, 1.0))
sphere_surface_3 = gs.surfaces.Default(color=(0.2, 0.4, 0.9, 1.0))

sphere_1 = scene.add_entity(
    material=sphere_material,
    morph=gs.morphs.Sphere(pos=(-5.0, -4.0, 2.5), radius=0.35),
    surface=sphere_surface_1,
)

sphere_2 = scene.add_entity(
    material=sphere_material,
    morph=gs.morphs.Sphere(pos=(0.5, 3.5, 3.0), radius=0.4),
    surface=sphere_surface_2,
)

sphere_3 = scene.add_entity(
    material=sphere_material,
    morph=gs.morphs.Sphere(pos=(4.5, -1.5, 2.8), radius=0.3),
    surface=sphere_surface_3,
)

camera = scene.add_camera(
    res=(1280, 720),
    pos=(14.0, 14.0, 9.0),
    lookat=(0.0, 0.0, 0.0),
    fov=50,
)

scene.build()

for step in range(1000):
    scene.step()
    if step % 100 == 0:
        p1 = sphere_1.get_pos()
        p2 = sphere_2.get_pos()
        p3 = sphere_3.get_pos()
        print(f"step={step:04d} sphere_1={p1} sphere_2={p2} sphere_3={p3}")
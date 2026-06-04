"""
User Query: Create a sandcastle on uneven terrain and simulate part of the structure collapsing when a heavy rigid block rolls into it from a slope.
task_id: s1_mpm_sand_complex_002
"""

import genesis as gs
import math

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=10,
        gravity=(0.0, 0.0, -9.81),
    ),
    mpm_options=gs.options.MPMOptions(
        lower_bound=(-8.0, -6.0, -0.5),
        upper_bound=(8.0, 6.0, 4.0),
    ),
    rigid_options=gs.options.RigidOptions(
        dt=0.005,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(7.0, -7.0, 4.5),
        camera_lookat=(0.5, 0.0, 0.8),
        camera_fov=45,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

terrain = scene.add_entity(
    gs.morphs.Terrain(
        pos=(0.0, 0.0, 0.0),
        n_subterrains=(2, 2),
        subterrain_size=(6.0, 6.0),
        horizontal_scale=0.25,
        vertical_scale=0.005,
        subterrain_types=[
            ["sloped_terrain", "wave_terrain"],
            ["flat_terrain", "fractal_terrain"],
        ],
    )
)

sand_material = gs.materials.MPM.Sand(sampler="regular")

castle_base = scene.add_entity(
    material=sand_material,
    morph=gs.morphs.Box(
        pos=(0.6, 0.0, 0.38),
        size=(1.6, 1.2, 0.7),
    ),
    surface=gs.surfaces.Rough(color=(0.88, 0.79, 0.58, 1.0)),
)

tower_1 = scene.add_entity(
    material=sand_material,
    morph=gs.morphs.Cylinder(
        pos=(0.0, -0.42, 0.95),
        radius=0.18,
        height=1.1,
    ),
    surface=gs.surfaces.Rough(color=(0.90, 0.80, 0.60, 1.0)),
)

tower_2 = scene.add_entity(
    material=sand_material,
    morph=gs.morphs.Cylinder(
        pos=(0.0, 0.42, 0.95),
        radius=0.18,
        height=1.1,
    ),
    surface=gs.surfaces.Rough(color=(0.90, 0.80, 0.60, 1.0)),
)

tower_3 = scene.add_entity(
    material=sand_material,
    morph=gs.morphs.Cylinder(
        pos=(1.15, -0.42, 0.95),
        radius=0.18,
        height=1.1,
    ),
    surface=gs.surfaces.Rough(color=(0.90, 0.80, 0.60, 1.0)),
)

tower_4 = scene.add_entity(
    material=sand_material,
    morph=gs.morphs.Cylinder(
        pos=(1.15, 0.42, 0.95),
        radius=0.18,
        height=1.1,
    ),
    surface=gs.surfaces.Rough(color=(0.90, 0.80, 0.60, 1.0)),
)

front_wall = scene.add_entity(
    material=sand_material,
    morph=gs.morphs.Box(
        pos=(0.58, 0.0, 0.78),
        size=(0.95, 0.16, 0.45),
    ),
    surface=gs.surfaces.Rough(color=(0.89, 0.79, 0.59, 1.0)),
)

side_wall_left = scene.add_entity(
    material=sand_material,
    morph=gs.morphs.Box(
        pos=(0.58, -0.50, 0.78),
        size=(1.10, 0.14, 0.42),
    ),
    surface=gs.surfaces.Rough(color=(0.89, 0.79, 0.59, 1.0)),
)

side_wall_right = scene.add_entity(
    material=sand_material,
    morph=gs.morphs.Box(
        pos=(0.58, 0.50, 0.78),
        size=(1.10, 0.14, 0.42),
    ),
    surface=gs.surfaces.Rough(color=(0.89, 0.79, 0.59, 1.0)),
)

rear_wall = scene.add_entity(
    material=sand_material,
    morph=gs.morphs.Box(
        pos=(1.05, 0.0, 0.78),
        size=(0.20, 1.0, 0.42),
    ),
    surface=gs.surfaces.Rough(color=(0.89, 0.79, 0.59, 1.0)),
)

gate_arch = scene.add_entity(
    material=sand_material,
    morph=gs.morphs.Box(
        pos=(0.18, 0.0, 0.98),
        size=(0.20, 0.36, 0.18),
    ),
    surface=gs.surfaces.Rough(color=(0.91, 0.81, 0.61, 1.0)),
)

central_keep = scene.add_entity(
    material=sand_material,
    morph=gs.morphs.Box(
        pos=(0.62, 0.0, 1.18),
        size=(0.45, 0.45, 0.55),
    ),
    surface=gs.surfaces.Rough(color=(0.92, 0.82, 0.62, 1.0)),
)

impact_ramp_marker = scene.add_entity(
    material=gs.materials.Rigid(
        rho=80.0,
        friction=1.2,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    morph=gs.morphs.Box(
        pos=(-2.6, 0.0, 1.55),
        size=(0.2, 0.2, 0.2),
    ),
    surface=gs.surfaces.Glass(color=(0.7, 0.8, 1.0, 0.2)),
)

block = scene.add_entity(
    material=gs.materials.Rigid(
        rho=1200.0,
        friction=1.8,
        coup_friction=0.2,
        coup_restitution=0.0,
    ),
    morph=gs.morphs.Box(
        pos=(-2.8, 0.0, 2.0),
        size=(0.7, 0.7, 0.7),
    ),
    surface=gs.surfaces.Iron(color=(0.45, 0.47, 0.52, 1.0)),
)

cam = scene.add_camera(
    res=(1280, 720),
    pos=(7.0, -7.0, 4.5),
    lookat=(0.5, 0.0, 0.8),
    fov=45,
)

scene.build()

cam.start_recording()

for i in range(1200):
    scene.step()
    if i % 2 == 0:
        cam.render()

cam.stop_recording(save_to_filename="s1_mpm_sand_complex_002.mp4")
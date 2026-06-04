"""
User Query: Generate an uneven rocky terrain using gs.morphs.Terrain (use fractal_terrain and random_uniform_terrain subtypes). Drop several rigid cubes onto different locations to observe how they settle.
task_id: s1_terrain_medium_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    rigid_options=gs.options.RigidOptions(
        gravity=(0.0, 0.0, -9.81),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

terrain = scene.add_entity(
    gs.morphs.Terrain(
        pos=(0.0, 0.0, 0.0),
        n_subterrains=(2, 2),
        subterrain_size=(6.0, 6.0),
        horizontal_scale=0.25,
        vertical_scale=0.02,
        subterrain_types=[
            ["fractal_terrain", "random_uniform_terrain"],
            ["random_uniform_terrain", "fractal_terrain"],
        ],
    )
)

cube_material = gs.materials.Rigid(
    rho=200.0,
    friction=1.2,
    coup_friction=0.1,
    coup_restitution=0.0,
)

cube_surface_colors = [
    (0.85, 0.25, 0.25, 1.0),
    (0.25, 0.85, 0.25, 1.0),
    (0.25, 0.35, 0.9, 1.0),
    (0.9, 0.75, 0.2, 1.0),
    (0.7, 0.3, 0.85, 1.0),
    (0.2, 0.8, 0.8, 1.0),
]

cube_positions = [
    (-4.0, -4.0, 2.5),
    (-1.5, -2.0, 3.0),
    (1.5, -3.0, 2.8),
    (-3.0, 2.0, 3.2),
    (0.5, 1.0, 2.6),
    (3.0, 3.0, 3.4),
]

cube_sizes = [
    (0.45, 0.45, 0.45),
    (0.55, 0.55, 0.55),
    (0.40, 0.40, 0.40),
    (0.60, 0.60, 0.60),
    (0.50, 0.50, 0.50),
    (0.48, 0.48, 0.48),
]

for pos, size, color in zip(cube_positions, cube_sizes, cube_surface_colors):
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=pos,
            size=size,
        ),
        material=cube_material,
        surface=gs.surfaces.Rough(color=color),
    )

scene.build()

for _ in range(800):
    scene.step()
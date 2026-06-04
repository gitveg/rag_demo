"""
User Query: Create a scene with a flat sand layer (MPM.Sand inside a Box container). Drop a cloth sheet (use gs.morphs.Mesh(file="meshes/cloth.obj") with FEM.Cloth material) above the sand and let it fall and drape over the sand surface.
task_id: s1_cross_domain_complex_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.005),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

wall_thickness = 0.1
container_half_size = 1.0
wall_height = 0.6
sand_top_z = 0.22

scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, wall_thickness * 0.5),
        size=(2.2, 2.2, wall_thickness),
    ),
    material=gs.materials.Rigid(rho=400.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Rough(color=(0.45, 0.45, 0.48, 1.0)),
)

scene.add_entity(
    gs.morphs.Box(
        pos=(container_half_size + wall_thickness * 0.5, 0.0, wall_height * 0.5),
        size=(wall_thickness, 2.2, wall_height),
    ),
    material=gs.materials.Rigid(rho=400.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Rough(color=(0.45, 0.45, 0.48, 1.0)),
)

scene.add_entity(
    gs.morphs.Box(
        pos=(-(container_half_size + wall_thickness * 0.5), 0.0, wall_height * 0.5),
        size=(wall_thickness, 2.2, wall_height),
    ),
    material=gs.materials.Rigid(rho=400.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Rough(color=(0.45, 0.45, 0.48, 1.0)),
)

scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, container_half_size + wall_thickness * 0.5, wall_height * 0.5),
        size=(2.2, wall_thickness, wall_height),
    ),
    material=gs.materials.Rigid(rho=400.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Rough(color=(0.45, 0.45, 0.48, 1.0)),
)

scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, -(container_half_size + wall_thickness * 0.5), wall_height * 0.5),
        size=(2.2, wall_thickness, wall_height),
    ),
    material=gs.materials.Rigid(rho=400.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Rough(color=(0.45, 0.45, 0.48, 1.0)),
)

scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, sand_top_z * 0.5 + wall_thickness),
        size=(1.8, 1.8, sand_top_z),
    ),
    material=gs.materials.MPM.Sand(sampler="regular"),
    surface=gs.surfaces.Rough(color=(0.82, 0.72, 0.50, 1.0)),
)

scene.add_entity(
    gs.morphs.Mesh(
        file="meshes/cloth.obj",
        pos=(0.0, 0.0, 0.7),
        scale=1.6,
    ),
    material=gs.materials.FEM.Cloth(
        rho=0.5,
        E=5e4,
        nu=0.49,
        thickness=0.001,
        model="stable_neohookean",
    ),
    surface=gs.surfaces.Default(color=(0.25, 0.55, 0.95, 1.0)),
)

scene.build()

for _ in range(1200):
    scene.step()
"""
User Query: Fill a transparent cubical tank halfway with liquid particles and observe the fluid settling under gravity.
task_id: s1_sph_fluid_medium_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.005),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

tank_center = (0.0, 0.0, 0.5)
tank_size = 1.0
wall_thickness = 0.05
wall_height = tank_size
inner_half = tank_size * 0.5
outer_half = inner_half + wall_thickness * 0.5

wall_material = gs.materials.Rigid(rho=200.0, friction=0.6, coup_friction=0.1, coup_restitution=0.0)
glass_surface = gs.surfaces.Glass(color=(0.7, 0.9, 1.0, 0.35))

scene.add_entity(
    gs.morphs.Box(
        pos=(tank_center[0], tank_center[1], wall_thickness * 0.5),
        size=(tank_size + 2.0 * wall_thickness, tank_size + 2.0 * wall_thickness, wall_thickness),
    ),
    material=wall_material,
    surface=glass_surface,
)

scene.add_entity(
    gs.morphs.Box(
        pos=(tank_center[0] + outer_half, tank_center[1], wall_height * 0.5),
        size=(wall_thickness, tank_size + 2.0 * wall_thickness, wall_height),
    ),
    material=wall_material,
    surface=glass_surface,
)

scene.add_entity(
    gs.morphs.Box(
        pos=(tank_center[0] - outer_half, tank_center[1], wall_height * 0.5),
        size=(wall_thickness, tank_size + 2.0 * wall_thickness, wall_height),
    ),
    material=wall_material,
    surface=glass_surface,
)

scene.add_entity(
    gs.morphs.Box(
        pos=(tank_center[0], tank_center[1] + outer_half, wall_height * 0.5),
        size=(tank_size, wall_thickness, wall_height),
    ),
    material=wall_material,
    surface=glass_surface,
)

scene.add_entity(
    gs.morphs.Box(
        pos=(tank_center[0], tank_center[1] - outer_half, wall_height * 0.5),
        size=(tank_size, wall_thickness, wall_height),
    ),
    material=wall_material,
    surface=glass_surface,
)

scene.add_entity(
    gs.morphs.Box(
        pos=(tank_center[0], tank_center[1], 0.275),
        size=(0.84, 0.84, 0.45),
    ),
    material=gs.materials.SPH.Liquid(sampler="regular"),
    surface=gs.surfaces.Default(color=(0.2, 0.45, 0.95, 0.9)),
)

scene.add_camera(
    pos=(2.4, -2.0, 1.8),
    lookat=(0.0, 0.0, 0.5),
    res=(960, 640),
)

scene.build()

for _ in range(600):
    scene.step()
"""
User Query: Drop a rigid sphere into a container filled with water and simulate the splash.
task_id: s1_cross_domain_simple_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=10,
        gravity=(0.0, 0.0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(4.0, -4.0, 3.0),
        camera_lookat=(0.0, 0.0, 0.8),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(
        rho=2000,
        friction=0.8,
        restitution=0.1,
    ),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

wall_thickness = 0.08
container_height = 1.2
container_inner = 1.6
wall_height_center = container_height * 0.5

rigid_mat = gs.materials.Rigid(
    rho=1200,
    friction=0.4,
    restitution=0.15,
)

glass_surface = gs.surfaces.Glass(color=(0.8, 0.9, 1.0, 0.35))

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, wall_height_center),
        size=(container_inner + 2 * wall_thickness, container_inner + 2 * wall_thickness, wall_thickness),
    ),
    material=rigid_mat,
    surface=glass_surface,
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(container_inner * 0.5 + wall_thickness * 0.5, 0.0, wall_height_center),
        size=(wall_thickness, container_inner + 2 * wall_thickness, container_height),
    ),
    material=rigid_mat,
    surface=glass_surface,
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-(container_inner * 0.5 + wall_thickness * 0.5), 0.0, wall_height_center),
        size=(wall_thickness, container_inner + 2 * wall_thickness, container_height),
    ),
    material=rigid_mat,
    surface=glass_surface,
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, container_inner * 0.5 + wall_thickness * 0.5, wall_height_center),
        size=(container_inner, wall_thickness, container_height),
    ),
    material=rigid_mat,
    surface=glass_surface,
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, -(container_inner * 0.5 + wall_thickness * 0.5), wall_height_center),
        size=(container_inner, wall_thickness, container_height),
    ),
    material=rigid_mat,
    surface=glass_surface,
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.42),
        size=(1.35, 1.35, 0.7),
    ),
    material=gs.materials.SPH.Liquid(sampler="regular"),
    surface=gs.surfaces.Glass(color=(0.2, 0.5, 1.0, 0.55)),
)

scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(0.0, 0.0, 1.8),
        radius=0.18,
    ),
    material=gs.materials.Rigid(
        rho=3500,
        friction=0.35,
        restitution=0.1,
    ),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

cam = scene.add_camera(
    pos=(3.2, -3.2, 2.2),
    lookat=(0.0, 0.0, 0.7),
    res=(1280, 720),
    fov=50,
)

scene.build()

for i in range(600):
    scene.step()
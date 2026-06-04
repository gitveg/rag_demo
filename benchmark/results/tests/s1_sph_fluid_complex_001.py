"""
User Query: Create a scene with a rigid sphere dropped from height into a container filled with water. The sphere should splash into the water and sink to the bottom while water splashes outward.
task_id: s1_sph_fluid_complex_001
"""

import genesis as gs


gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=10,
        gravity=(0, 0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(4.0, -4.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.7),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

ground = scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.1),
    surface=gs.surfaces.Rough(color=(0.45, 0.45, 0.45, 1.0)),
)

wall_thickness = 0.08
container_height = 1.2
inner_half = 0.8
wall_height_center = container_height / 2.0

bottom = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, wall_thickness / 2.0),
        size=(2 * inner_half + 2 * wall_thickness, 2 * inner_half + 2 * wall_thickness, wall_thickness),
    ),
    material=gs.materials.Rigid(rho=1200, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

wall_x_pos = inner_half + wall_thickness / 2.0
wall_y_pos = inner_half + wall_thickness / 2.0

wall_px = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(wall_x_pos, 0.0, wall_height_center),
        size=(wall_thickness, 2 * inner_half + 2 * wall_thickness, container_height),
    ),
    material=gs.materials.Rigid(rho=1200, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Glass(color=(0.7, 0.85, 1.0, 0.35)),
)

wall_nx = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-wall_x_pos, 0.0, wall_height_center),
        size=(wall_thickness, 2 * inner_half + 2 * wall_thickness, container_height),
    ),
    material=gs.materials.Rigid(rho=1200, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Glass(color=(0.7, 0.85, 1.0, 0.35)),
)

wall_py = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, wall_y_pos, wall_height_center),
        size=(2 * inner_half, wall_thickness, container_height),
    ),
    material=gs.materials.Rigid(rho=1200, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Glass(color=(0.7, 0.85, 1.0, 0.35)),
)

wall_ny = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, -wall_y_pos, wall_height_center),
        size=(2 * inner_half, wall_thickness, container_height),
    ),
    material=gs.materials.Rigid(rho=1200, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Glass(color=(0.7, 0.85, 1.0, 0.35)),
)

water = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.45),
        size=(1.45, 1.45, 0.75),
    ),
    material=gs.materials.SPH.Liquid(sampler="regular"),
    surface=gs.surfaces.Glass(color=(0.35, 0.6, 1.0, 0.55)),
)

sphere = scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(0.0, 0.0, 1.55),
        radius=0.18,
    ),
    material=gs.materials.Rigid(rho=3500, friction=0.4, restitution=0.05),
    surface=gs.surfaces.Gold(color=(1.0, 0.84, 0.0, 1.0)),
)

cam = scene.add_camera(
    res=(1280, 720),
    pos=(3.8, -3.8, 2.2),
    lookat=(0.0, 0.0, 0.7),
    fov=45,
)

scene.build()

for i in range(1200):
    scene.step()
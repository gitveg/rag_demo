"""
User Query: Pour water from a small height into an empty container and simulate realistic splashing.
task_id: s1_sph_fluid_simple_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=8,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.2, -2.8, 2.2),
        camera_lookat=(0.0, 0.2, 0.5),
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
    surface=gs.surfaces.Rough(color=(0.85, 0.85, 0.85, 1.0)),
)

wall_thickness = 0.04
container_height = 0.5
inner_size = 0.5
wall_height_center = container_height / 2.0
half_extent = inner_size / 2.0 + wall_thickness / 2.0

rigid_mat = gs.materials.Rigid(
    rho=1500,
    friction=0.6,
    restitution=0.05,
)

container_color = gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0))

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, wall_thickness / 2.0),
        size=(inner_size + 2 * wall_thickness, inner_size + 2 * wall_thickness, wall_thickness),
    ),
    material=rigid_mat,
    surface=container_color,
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(half_extent, 0.0, wall_height_center),
        size=(wall_thickness, inner_size + 2 * wall_thickness, container_height),
    ),
    material=rigid_mat,
    surface=container_color,
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-half_extent, 0.0, wall_height_center),
        size=(wall_thickness, inner_size + 2 * wall_thickness, container_height),
    ),
    material=rigid_mat,
    surface=container_color,
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, half_extent, wall_height_center),
        size=(inner_size, wall_thickness, container_height),
    ),
    material=rigid_mat,
    surface=container_color,
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, -half_extent, wall_height_center),
        size=(inner_size, wall_thickness, container_height),
    ),
    material=rigid_mat,
    surface=container_color,
)

scene.add_entity(
    morph=gs.morphs.Cylinder(
        pos=(-0.55, 0.0, 0.95),
        radius=0.08,
        height=0.22,
    ),
    material=gs.materials.Rigid(
        rho=1200,
        friction=0.5,
        restitution=0.05,
    ),
    surface=gs.surfaces.Aluminium(color=(0.9, 0.9, 0.9, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-0.33, 0.0, 0.72),
        size=(0.32, 0.08, 0.08),
    ),
    material=gs.materials.Rigid(
        rho=1200,
        friction=0.4,
        restitution=0.05,
    ),
    surface=gs.surfaces.Aluminium(color=(0.88, 0.88, 0.9, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-0.14, 0.0, 0.67),
        size=(0.06, 0.06, 0.18),
    ),
    material=gs.materials.Rigid(
        rho=1200,
        friction=0.4,
        restitution=0.05,
    ),
    surface=gs.surfaces.Aluminium(color=(0.88, 0.88, 0.9, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-0.03, 0.0, 0.62),
        size=(0.16, 0.05, 0.05),
    ),
    material=gs.materials.Rigid(
        rho=1200,
        friction=0.35,
        restitution=0.05,
    ),
    surface=gs.surfaces.Aluminium(color=(0.92, 0.92, 0.94, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-0.02, 0.0, 0.52),
        size=(0.06, 0.05, 0.18),
    ),
    material=gs.materials.Rigid(
        rho=1200,
        friction=0.35,
        restitution=0.05,
    ),
    surface=gs.surfaces.Aluminium(color=(0.92, 0.92, 0.94, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-0.08, 0.0, 1.02),
        size=(0.14, 0.14, 0.14),
    ),
    material=gs.materials.SPH.Liquid(sampler="regular"),
    surface=gs.surfaces.Glass(color=(0.35, 0.6, 1.0, 0.5)),
)

scene.build()

for _ in range(1200):
    scene.step()
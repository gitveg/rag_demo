"""
User Query: Create two streams of colored liquid flowing from opposite sides into a bowl and show the liquids mixing together.
task_id: s1_sph_fluid_medium_002
"""

import genesis as gs
import math

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=10,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(0.0, -4.8, 2.3),
        camera_lookat=(0.0, 0.0, 0.8),
        camera_fov=45,
    ),
    renderer=gs.options.renderers.RayTracer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=2000, friction=0.8, restitution=0.1),
    surface=gs.surfaces.Rough(color=(0.82, 0.82, 0.82, 1.0)),
)

# Bowl built from rigid primitives: bottom + four walls
bowl_center = (0.0, 0.0, 0.25)
bowl_half_w = 0.7
bowl_half_d = 0.7
wall_thickness = 0.08
bottom_thickness = 0.10
wall_height = 0.55

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(bowl_center[0], bowl_center[1], bottom_thickness * 0.5),
        size=(2 * bowl_half_w, 2 * bowl_half_d, bottom_thickness),
    ),
    material=gs.materials.Rigid(rho=2500, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Iron(color=(0.45, 0.46, 0.50, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(bowl_center[0] + bowl_half_w + wall_thickness * 0.5, bowl_center[1], bottom_thickness + wall_height * 0.5),
        size=(wall_thickness, 2 * bowl_half_d + 2 * wall_thickness, wall_height),
    ),
    material=gs.materials.Rigid(rho=2500, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Iron(color=(0.48, 0.48, 0.52, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(bowl_center[0] - bowl_half_w - wall_thickness * 0.5, bowl_center[1], bottom_thickness + wall_height * 0.5),
        size=(wall_thickness, 2 * bowl_half_d + 2 * wall_thickness, wall_height),
    ),
    material=gs.materials.Rigid(rho=2500, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Iron(color=(0.48, 0.48, 0.52, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(bowl_center[0], bowl_center[1] + bowl_half_d + wall_thickness * 0.5, bottom_thickness + wall_height * 0.5),
        size=(2 * bowl_half_w, wall_thickness, wall_height),
    ),
    material=gs.materials.Rigid(rho=2500, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Iron(color=(0.50, 0.50, 0.54, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(bowl_center[0], bowl_center[1] - bowl_half_d - wall_thickness * 0.5, bottom_thickness + wall_height * 0.5),
        size=(2 * bowl_half_w, wall_thickness, wall_height),
    ),
    material=gs.materials.Rigid(rho=2500, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Iron(color=(0.50, 0.50, 0.54, 1.0)),
)

# Decorative glass outer shell to make it look more bowl-like
scene.add_entity(
    morph=gs.morphs.Box(
        pos=(bowl_center[0], bowl_center[1], bottom_thickness + wall_height * 0.5),
        size=(2.0, 2.0, wall_height + 0.04),
    ),
    material=gs.materials.Rigid(rho=1200, friction=0.2, restitution=0.05),
    surface=gs.surfaces.Glass(color=(0.8, 0.9, 1.0, 0.18)),
)

# Left nozzle and support
scene.add_entity(
    morph=gs.morphs.Cylinder(
        pos=(-1.35, 0.0, 1.05),
        radius=0.08,
        height=0.55,
    ),
    material=gs.materials.Rigid(rho=1500, friction=0.6, restitution=0.1),
    surface=gs.surfaces.Aluminium(color=(0.90, 0.25, 0.25, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-0.95, 0.0, 0.98),
        size=(0.85, 0.12, 0.12),
    ),
    material=gs.materials.Rigid(rho=1500, friction=0.6, restitution=0.1),
    surface=gs.surfaces.Aluminium(color=(0.92, 0.30, 0.30, 1.0)),
)

# Right nozzle and support
scene.add_entity(
    morph=gs.morphs.Cylinder(
        pos=(1.35, 0.0, 1.05),
        radius=0.08,
        height=0.55,
    ),
    material=gs.materials.Rigid(rho=1500, friction=0.6, restitution=0.1),
    surface=gs.surfaces.Aluminium(color=(0.20, 0.40, 0.95, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.95, 0.0, 0.98),
        size=(0.85, 0.12, 0.12),
    ),
    material=gs.materials.Rigid(rho=1500, friction=0.6, restitution=0.1),
    surface=gs.surfaces.Aluminium(color=(0.25, 0.45, 0.95, 1.0)),
)

# Liquid stream from left
scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-0.68, -0.10, 1.02),
        size=(0.42, 0.18, 0.65),
    ),
    material=gs.materials.SPH.Liquid(sampler="regular"),
    surface=gs.surfaces.Glass(color=(0.95, 0.20, 0.20, 0.75)),
)

# Liquid stream from right
scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.68, 0.10, 1.02),
        size=(0.42, 0.18, 0.65),
    ),
    material=gs.materials.SPH.Liquid(sampler="regular"),
    surface=gs.surfaces.Glass(color=(0.20, 0.40, 0.98, 0.75)),
)

cam = scene.add_camera(
    pos=(0.0, -4.2, 2.1),
    lookat=(0.0, 0.0, 0.75),
    fov=42,
)

scene.build()
scene.reset()

for i in range(900):
    scene.step()
    if i % 3 == 0:
        cam.render()
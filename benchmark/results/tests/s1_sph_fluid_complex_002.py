"""
User Query: Build a kitchen sink scene where water continuously flows from a faucet into a transparent glass container, eventually overflowing onto the floor with visible splashes and fluid interaction.
task_id: s1_sph_fluid_complex_002
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=8,
        gravity=(0.0, 0.0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.2, -2.8, 2.2),
        camera_lookat=(0.0, 0.0, 0.8),
        camera_fov=50,
    ),
    renderer=gs.options.renderers.RayTracer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Rough(color=(0.72, 0.72, 0.72, 1.0)),
)

counter = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.45),
        size=(2.2, 1.2, 0.9),
    ),
    material=gs.materials.Rigid(rho=1200, friction=0.8, restitution=0.02),
    surface=gs.surfaces.Rough(color=(0.82, 0.80, 0.76, 1.0)),
)

sink_base = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.80),
        size=(0.95, 0.58, 0.10),
    ),
    material=gs.materials.Rigid(rho=7800, friction=0.6, restitution=0.02),
    surface=gs.surfaces.Iron(color=(0.75, 0.77, 0.80, 1.0)),
)

sink_basin_bottom = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.73),
        size=(0.72, 0.42, 0.03),
    ),
    material=gs.materials.Rigid(rho=7800, friction=0.5, restitution=0.02),
    surface=gs.surfaces.Iron(color=(0.70, 0.72, 0.75, 1.0)),
)

wall_thickness = 0.03
wall_height = 0.20

sink_wall_left = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.225, 0.83),
        size=(0.72, wall_thickness, wall_height),
    ),
    material=gs.materials.Rigid(rho=7800, friction=0.5, restitution=0.02),
    surface=gs.surfaces.Iron(color=(0.72, 0.74, 0.77, 1.0)),
)

sink_wall_right = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, -0.225, 0.83),
        size=(0.72, wall_thickness, wall_height),
    ),
    material=gs.materials.Rigid(rho=7800, friction=0.5, restitution=0.02),
    surface=gs.surfaces.Iron(color=(0.72, 0.74, 0.77, 1.0)),
)

sink_wall_back = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-0.345, 0.0, 0.83),
        size=(wall_thickness, 0.42, wall_height),
    ),
    material=gs.materials.Rigid(rho=7800, friction=0.5, restitution=0.02),
    surface=gs.surfaces.Iron(color=(0.72, 0.74, 0.77, 1.0)),
)

sink_wall_front = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.345, 0.0, 0.83),
        size=(wall_thickness, 0.42, wall_height),
    ),
    material=gs.materials.Rigid(rho=7800, friction=0.5, restitution=0.02),
    surface=gs.surfaces.Iron(color=(0.72, 0.74, 0.77, 1.0)),
)

faucet_stem = scene.add_entity(
    morph=gs.morphs.Cylinder(
        pos=(-0.18, 0.0, 1.08),
        radius=0.03,
        height=0.32,
    ),
    material=gs.materials.Rigid(rho=7800, friction=0.4, restitution=0.02),
    surface=gs.surfaces.Aluminium(color=(0.90, 0.91, 0.93, 1.0)),
)

faucet_spout = scene.add_entity(
    morph=gs.morphs.Cylinder(
        pos=(0.02, 0.0, 1.19),
        radius=0.022,
        height=0.40,
    ),
    material=gs.materials.Rigid(rho=7800, friction=0.4, restitution=0.02),
    surface=gs.surfaces.Aluminium(color=(0.90, 0.91, 0.93, 1.0)),
)

glass_bottom = scene.add_entity(
    morph=gs.morphs.Cylinder(
        pos=(0.18, 0.0, 0.775),
        radius=0.12,
        height=0.015,
    ),
    material=gs.materials.Rigid(rho=2500, friction=0.35, restitution=0.03),
    surface=gs.surfaces.Glass(color=(0.85, 0.95, 1.00, 0.35)),
)

glass_wall_1 = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.18 + 0.105, 0.0, 0.925),
        size=(0.01, 0.24, 0.30),
    ),
    material=gs.materials.Rigid(rho=2500, friction=0.35, restitution=0.03),
    surface=gs.surfaces.Glass(color=(0.85, 0.95, 1.00, 0.28)),
)

glass_wall_2 = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.18 - 0.105, 0.0, 0.925),
        size=(0.01, 0.24, 0.30),
    ),
    material=gs.materials.Rigid(rho=2500, friction=0.35, restitution=0.03),
    surface=gs.surfaces.Glass(color=(0.85, 0.95, 1.00, 0.28)),
)

glass_wall_3 = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.18, 0.105, 0.925),
        size=(0.22, 0.01, 0.30),
    ),
    material=gs.materials.Rigid(rho=2500, friction=0.35, restitution=0.03),
    surface=gs.surfaces.Glass(color=(0.85, 0.95, 1.00, 0.28)),
)

glass_wall_4 = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.18, -0.105, 0.925),
        size=(0.22, 0.01, 0.30),
    ),
    material=gs.materials.Rigid(rho=2500, friction=0.35, restitution=0.03),
    surface=gs.surfaces.Glass(color=(0.85, 0.95, 1.00, 0.28)),
)

water_volume = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.02, 0.0, 1.03),
        size=(0.055, 0.055, 0.40),
    ),
    material=gs.materials.SPH.Liquid(sampler="regular"),
    surface=gs.surfaces.Glass(color=(0.35, 0.60, 1.00, 0.65)),
)

scene.add_camera(
    res=(1280, 720),
    pos=(3.2, -2.8, 2.2),
    lookat=(0.0, 0.0, 0.9),
    fov=50,
)

scene.build()

for step in range(2400):
    scene.step()
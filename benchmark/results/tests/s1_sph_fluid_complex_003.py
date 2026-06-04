"""
User Query: Simulate a high-speed stream of liquid being poured into a bowl from an angle, causing the fluid to swirl and splash against the inner walls.
task_id: s1_sph_fluid_complex_003
"""

import genesis as gs
import math

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=8,
        gravity=(0.0, 0.0, -9.81),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=2000, friction=0.8, restitution=0.1),
    surface=gs.surfaces.Rough(color=(0.82, 0.82, 0.82, 1.0)),
)

wall_thickness = 0.06
bowl_outer_radius = 0.95
bowl_height = 0.55
inner_radius = 0.68
bottom_thickness = 0.10

scene.add_entity(
    gs.morphs.Cylinder(
        pos=(0.0, 0.0, bowl_height * 0.5),
        radius=bowl_outer_radius,
        height=bowl_height,
    ),
    material=gs.materials.Rigid(rho=2700, friction=0.7, restitution=0.05),
    surface=gs.surfaces.Iron(color=(0.45, 0.47, 0.52, 1.0)),
)

scene.add_entity(
    gs.morphs.Cylinder(
        pos=(0.0, 0.0, bottom_thickness + (bowl_height - bottom_thickness) * 0.5),
        radius=inner_radius,
        height=bowl_height - bottom_thickness,
    ),
    material=gs.materials.Rigid(rho=2700, friction=0.7, restitution=0.05),
    surface=gs.surfaces.Default(color=(0.08, 0.08, 0.08, 1.0)),
)

liquid = scene.add_entity(
    gs.morphs.Box(
        pos=(1.05, 0.0, 1.05),
        size=(0.18, 0.18, 0.65),
    ),
    material=gs.materials.SPH.Liquid(sampler="regular"),
    surface=gs.surfaces.Glass(color=(0.2, 0.55, 0.95, 0.5)),
)

guide_tube = scene.add_entity(
    gs.morphs.Cylinder(
        pos=(0.95, -0.05, 1.00),
        radius=0.07,
        height=0.70,
    ),
    material=gs.materials.Rigid(rho=1200, friction=0.3, restitution=0.05),
    surface=gs.surfaces.Aluminium(color=(0.85, 0.85, 0.88, 1.0)),
)

scene.add_force_field(
    gs.options.ForceField(
        type="constant",
        direction=(-0.95, 0.2, -0.25),
        strength=38.0,
    )
)

scene.add_force_field(
    gs.options.ForceField(
        type="vortex",
        axis=(0.0, 0.0, 1.0),
        strength=14.0,
    )
)

scene.add_force_field(
    gs.options.ForceField(
        type="turbulent",
        strength=3.0,
        frequency=2.5,
    )
)

cam = scene.add_camera(
    pos=(3.2, -2.2, 1.8),
    lookat=(0.0, 0.0, 0.55),
    res=(1280, 720),
    fov=45,
)

scene.build()

for i in range(900):
    angle = 0.35 + 0.08 * math.sin(i * 0.03)
    x = 0.95 + 0.02 * math.cos(i * 0.05)
    y = -0.05 + 0.03 * math.sin(i * 0.04)
    z = 1.00 + 0.01 * math.sin(i * 0.06)
    if hasattr(guide_tube, "set_pos"):
        guide_tube.set_pos((x, y, z))
    if hasattr(guide_tube, "set_quat"):
        half = angle * 0.5
        guide_tube.set_quat((0.0, math.sin(half), 0.0, math.cos(half)))
    scene.step()
    if i % 2 == 0:
        cam.render()
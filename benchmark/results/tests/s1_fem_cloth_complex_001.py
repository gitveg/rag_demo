"""
User Query: Simulate a cloth curtain hanging from a horizontal rod. A rigid sphere is thrown horizontally into the curtain, pushing it aside and passing through.
task_id: s1_fem_cloth_complex_001
"""

import genesis as gs
import numpy as np

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=10,
        gravity=(0.0, 0.0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(4.0, -6.0, 2.5),
        camera_lookat=(0.0, 0.0, 1.2),
        camera_fov=45,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(
        rho=200.0,
        friction=0.8,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

rod_length = 2.4
rod_radius = 0.04
rod_z = 1.9

scene.add_entity(
    gs.morphs.Cylinder(
        pos=(0.0, 0.0, rod_z),
        radius=rod_radius,
        height=rod_length,
    ),
    material=gs.materials.Rigid(
        rho=500.0,
        friction=0.6,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

curtain_width = 2.2
curtain_height = 1.6
curtain_top_z = rod_z - rod_radius - 0.02
curtain_center_z = curtain_top_z - curtain_height / 2.0
curtain_thickness = 0.02

cloth = scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, curtain_center_z),
        size=(curtain_thickness, curtain_width, curtain_height),
    ),
    material=gs.materials.FEM.Cloth(
        rho=0.5,
        E=5e4,
        nu=0.49,
        thickness=0.001,
        model="stable_neohookean",
    ),
    surface=gs.surfaces.Rough(color=(0.25, 0.45, 0.85, 1.0)),
)

sphere_radius = 0.14
sphere_start = (-1.8, 0.0, 1.1)

ball = scene.add_entity(
    gs.morphs.Sphere(
        pos=sphere_start,
        radius=sphere_radius,
    ),
    material=gs.materials.Rigid(
        rho=600.0,
        friction=0.4,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Gold(color=(1.0, 0.84, 0.0, 1.0)),
)

cam = scene.add_camera(
    res=(960, 640),
    pos=(4.2, -5.8, 2.5),
    lookat=(0.0, 0.0, 1.15),
    fov=45,
)

scene.build()

if hasattr(cloth, "set_pinned_vertices"):
    ny = 25
    nz = 33
    pinned = []
    for j in range(ny):
        pinned.append(j * nz + (nz - 1))
    cloth.set_pinned_vertices(pinned)
elif hasattr(cloth, "fix_particles"):
    cloth.fix_particles("top")
elif hasattr(cloth, "set_fixed"):
    cloth.set_fixed(True)

throw_speed = 8.0
if hasattr(ball, "set_velocity"):
    ball.set_velocity((throw_speed, 0.0, 0.0))
elif hasattr(ball, "set_vel"):
    ball.set_vel((throw_speed, 0.0, 0.0))
elif hasattr(ball, "set_linear_velocity"):
    ball.set_linear_velocity((throw_speed, 0.0, 0.0))

num_steps = 700

for i in range(num_steps):
    scene.step()
    if i % 10 == 0:
        cam.render()
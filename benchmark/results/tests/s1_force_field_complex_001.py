"""
User Query: Simulate a rigid ball inside a box. Apply a rotating force field around the vertical axis so the ball rolls in a circular path along the bottom of the box.
task_id: s1_force_field_complex_001
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(4.0, -4.0, 3.0),
        camera_lookat=(0.0, 0.0, 0.5),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(friction=1.0),
    surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8, 1.0)),
)

wall_thickness = 0.1
box_size = 2.0
wall_height = 0.6
half_extent = box_size / 2.0

# Bottom plate of the box
scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, wall_thickness / 2.0),
        size=(box_size, box_size, wall_thickness),
    ),
    material=gs.materials.Rigid(friction=1.2),
    surface=gs.surfaces.Rough(color=(0.35, 0.35, 0.4, 1.0)),
)

# Walls
scene.add_entity(
    gs.morphs.Box(
        pos=(half_extent + wall_thickness / 2.0, 0.0, wall_height / 2.0),
        size=(wall_thickness, box_size + 2.0 * wall_thickness, wall_height),
    ),
    material=gs.materials.Rigid(friction=1.0),
    surface=gs.surfaces.Iron(),
)

scene.add_entity(
    gs.morphs.Box(
        pos=(-half_extent - wall_thickness / 2.0, 0.0, wall_height / 2.0),
        size=(wall_thickness, box_size + 2.0 * wall_thickness, wall_height),
    ),
    material=gs.materials.Rigid(friction=1.0),
    surface=gs.surfaces.Iron(),
)

scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, half_extent + wall_thickness / 2.0, wall_height / 2.0),
        size=(box_size, wall_thickness, wall_height),
    ),
    material=gs.materials.Rigid(friction=1.0),
    surface=gs.surfaces.Iron(),
)

scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, -half_extent - wall_thickness / 2.0, wall_height / 2.0),
        size=(box_size, wall_thickness, wall_height),
    ),
    material=gs.materials.Rigid(friction=1.0),
    surface=gs.surfaces.Iron(),
)

ball_radius = 0.12
ball = scene.add_entity(
    gs.morphs.Sphere(
        pos=(0.55, 0.0, wall_thickness + ball_radius + 0.01),
        radius=ball_radius,
    ),
    material=gs.materials.Rigid(
        rho=400.0,
        friction=1.5,
        coup_friction=0.15,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Gold(),
)

scene.add_force_field(
    gs.force_fields.Vortex(
        direction=(0.0, 0.0, 1.0),
        strength_perpendicular=18.0,
    )
)

scene.build()

for step in range(1200):
    scene.step()

    if step % 100 == 0:
        pos = ball.get_pos()
        print(f"step={step:04d}, ball_pos=({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
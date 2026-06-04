"""
User Query: Create a storm scene with strong turbulent wind affecting hanging cloth, rolling rigid barrels, and falling debris at the same time.
task_id: s1_force_field_complex_002
"""

import genesis as gs
import math

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(8.0, -10.0, 6.0),
        camera_lookat=(0.0, 0.0, 2.0),
        camera_fov=50,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

ground = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(
        rho=200.0,
        friction=2.0,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Rough(color=(0.28, 0.30, 0.33, 1.0)),
)

platform = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 0.25), size=(12.0, 6.0, 0.5)),
    material=gs.materials.Rigid(
        rho=400.0,
        friction=1.8,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Iron(color=(0.35, 0.37, 0.40, 1.0)),
)

left_pole = scene.add_entity(
    gs.morphs.Box(pos=(-1.5, -1.8, 2.6), size=(0.18, 0.18, 5.2)),
    material=gs.materials.Rigid(
        rho=500.0,
        friction=1.0,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Iron(color=(0.45, 0.46, 0.48, 1.0)),
)

right_pole = scene.add_entity(
    gs.morphs.Box(pos=(-1.5, 1.8, 2.6), size=(0.18, 0.18, 5.2)),
    material=gs.materials.Rigid(
        rho=500.0,
        friction=1.0,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Iron(color=(0.45, 0.46, 0.48, 1.0)),
)

top_beam = scene.add_entity(
    gs.morphs.Box(pos=(-1.5, 0.0, 4.95), size=(0.18, 3.8, 0.18)),
    material=gs.materials.Rigid(
        rho=500.0,
        friction=1.0,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Iron(color=(0.50, 0.51, 0.53, 1.0)),
)

cloth = scene.add_entity(
    gs.morphs.Mesh(
        file="meshes/cloth.obj",
        pos=(-1.5, 0.0, 4.1),
        scale=2.2,
    ),
    material=gs.materials.FEM.Cloth(
        rho=0.5,
        E=5e4,
        nu=0.49,
        thickness=0.001,
        model="stable_neohookean",
    ),
    surface=gs.surfaces.Default(color=(0.12, 0.18, 0.65, 1.0)),
)

barrel_positions = [
    (1.0, -1.6, 0.75),
    (2.0, -0.5, 0.75),
    (2.8, 0.8, 0.75),
    (3.6, 1.7, 0.75),
]

barrels = []
for i, pos in enumerate(barrel_positions):
    barrel = scene.add_entity(
        gs.morphs.Cylinder(
            pos=pos,
            radius=0.35,
            height=0.9,
        ),
        material=gs.materials.Rigid(
            rho=220.0,
            friction=0.45,
            coup_friction=0.1,
            coup_restitution=0.0,
        ),
        surface=gs.surfaces.Aluminium(
            color=(0.72 - 0.05 * i, 0.72 - 0.04 * i, 0.78, 1.0)
        ),
    )
    barrels.append(barrel)

debris_specs = [
    ((-2.0, -1.0, 6.8), (0.22, 0.18, 0.15), (0.55, 0.30, 0.22, 1.0)),
    ((-0.8, 0.6, 7.4), (0.16, 0.28, 0.14), (0.50, 0.27, 0.20, 1.0)),
    ((0.4, -0.3, 8.0), (0.25, 0.12, 0.18), (0.58, 0.33, 0.24, 1.0)),
    ((1.6, 1.0, 7.2), (0.20, 0.20, 0.22), (0.48, 0.26, 0.18, 1.0)),
    ((2.7, -1.4, 8.5), (0.14, 0.24, 0.16), (0.60, 0.36, 0.25, 1.0)),
    ((3.5, 0.2, 7.7), (0.26, 0.16, 0.14), (0.52, 0.29, 0.21, 1.0)),
]

debris = []
for pos, size, color in debris_specs:
    piece = scene.add_entity(
        gs.morphs.Box(pos=pos, size=size),
        material=gs.materials.Rigid(
            rho=120.0,
            friction=0.6,
            coup_friction=0.1,
            coup_restitution=0.0,
        ),
        surface=gs.surfaces.Rough(color=color),
    )
    debris.append(piece)

scene.add_force_field(
    gs.force_fields.Constant(direction=(1.0, 0.15, 0.0), strength=28.0)
)
scene.add_force_field(
    gs.force_fields.Turbulence(strength=42.0, frequency=6.0)
)
scene.add_force_field(
    gs.force_fields.Vortex(direction=(0.0, 0.0, 1.0), strength_perpendicular=10.0)
)
scene.add_force_field(
    gs.force_fields.Noise(strength=8.0)
)

cam = scene.add_camera(
    res=(1280, 720),
    pos=(8.0, -10.0, 6.0),
    lookat=(0.0, 0.0, 2.0),
    fov=50,
)

scene.build()

for step in range(900):
    if step < 120:
        ramp = step / 120.0
    else:
        ramp = 1.0

    gust = 0.5 + 0.5 * math.sin(step * 0.08)
    side_push = 0.2 * math.sin(step * 0.11)

    for i, barrel in enumerate(barrels):
        phase = i * 0.8
        fx = (35.0 + 14.0 * math.sin(step * 0.07 + phase)) * ramp
        fy = (10.0 * math.cos(step * 0.09 + phase) + 8.0 * side_push) * ramp
        torque = (6.0 + 3.0 * math.sin(step * 0.13 + phase)) * ramp
        try:
            barrel.apply_force((fx, fy, 0.0))
        except Exception:
            pass
        try:
            barrel.apply_torque((0.0, torque, 0.0))
        except Exception:
            pass

    for i, piece in enumerate(debris):
        phase = i * 0.6
        fx = (18.0 + 20.0 * gust + 8.0 * math.sin(step * 0.17 + phase)) * ramp
        fy = (6.0 * math.cos(step * 0.21 + phase)) * ramp
        fz = (3.0 * math.sin(step * 0.19 + phase)) * ramp
        try:
            piece.apply_force((fx, fy, fz))
        except Exception:
            pass

    scene.step()

    if step % 3 == 0:
        cam.render()
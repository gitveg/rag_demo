"""
User Query: Define a central point that exerts a strong attractive radial force, pulling several surrounding objects toward it like a vacuum.
task_id: s1_force_field_complex_003
"""

import genesis as gs
import math

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(8.0, 8.0, 6.0),
        camera_lookat=(0.0, 0.0, 1.0),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.Entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.2),
        surface=gs.surfaces.Rough(color=(0.2, 0.2, 0.24, 1.0)),
    )
)

vacuum_center = (0.0, 0.0, 1.0)

scene.add_entity(
    gs.Entity(
        morph=gs.morphs.Sphere(pos=vacuum_center, radius=0.22),
        material=gs.materials.Rigid(rho=5000, friction=0.4, restitution=0.0),
        surface=gs.surfaces.Emission(color=(0.3, 0.8, 1.0, 1.0)),
    )
)

ring_radius = 3.0
heights = [0.35, 0.45, 0.55, 0.65, 0.4, 0.5, 0.6, 0.7]
colors = [
    (1.0, 0.3, 0.3, 1.0),
    (0.3, 1.0, 0.3, 1.0),
    (0.3, 0.5, 1.0, 1.0),
    (1.0, 0.8, 0.2, 1.0),
    (0.9, 0.3, 1.0, 1.0),
    (0.2, 1.0, 0.9, 1.0),
    (1.0, 0.5, 0.2, 1.0),
    (0.8, 0.8, 0.8, 1.0),
]

dynamic_bodies = []
for i in range(8):
    angle = 2.0 * math.pi * i / 8.0
    x = ring_radius * math.cos(angle)
    y = ring_radius * math.sin(angle)
    z = heights[i]

    if i % 2 == 0:
        entity = scene.add_entity(
            gs.Entity(
                morph=gs.morphs.Box(pos=(x, y, z), size=(0.35, 0.35, 0.35)),
                material=gs.materials.Rigid(rho=600, friction=0.5, restitution=0.1),
                surface=gs.surfaces.Default(color=colors[i]),
            )
        )
    else:
        entity = scene.add_entity(
            gs.Entity(
                morph=gs.morphs.Sphere(pos=(x, y, z), radius=0.2),
                material=gs.materials.Rigid(rho=700, friction=0.5, restitution=0.1),
                surface=gs.surfaces.Default(color=colors[i]),
            )
        )
    dynamic_bodies.append(entity)

scene.add_force_field(
    gs.options.ForceField(
        type="vortex",
        axis=(0.0, 0.0, 1.0),
        strength=18.0,
    )
)

scene.build()

center_xyz = gs.tensor(vacuum_center, dtype=gs.tc_float)
radial_strength = 140.0
vertical_lift = 8.0
damping_scale = 3.0
steps = 1200

for _ in range(steps):
    for body in dynamic_bodies:
        pos = body.get_pos()
        vel = body.get_vel()

        offset = center_xyz - pos
        dist = gs.norm(offset) + 1e-6
        direction = offset / dist

        force_mag = radial_strength / (dist * dist + 0.08)
        force = direction * force_mag

        upward = gs.tensor((0.0, 0.0, vertical_lift / (dist + 0.2)), dtype=gs.tc_float)
        damping = -damping_scale * vel

        body.apply_external_force(force + upward + damping)

    scene.step()
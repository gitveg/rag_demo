"""
User Query: Apply a constant sideways wind force to a lightweight sphere suspended in the air.
task_id: s1_force_field_simple_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, -3.0, 2.0),
        camera_lookat=(0.0, 0.0, 1.0),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=2000, friction=0.8, restitution=0.2),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

scene.add_entity(
    gs.morphs.Sphere(pos=(0.0, 0.0, 1.5), radius=0.12),
    material=gs.materials.Rigid(rho=80, friction=0.2, restitution=0.4),
    surface=gs.surfaces.Default(color=(0.3, 0.6, 1.0, 1.0)),
)

scene.add_force_field(
    gs.options.ForceField(
        type="constant",
        direction=(1.0, 0.0, 0.0),
        strength=8.0,
    )
)

scene.build()

for _ in range(600):
    scene.step()
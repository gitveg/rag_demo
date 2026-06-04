"""
User Query: A rigid sphere is pushed sideways by a constant wind force while falling.
task_id: s1_force_field_simple_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(4.0, -4.0, 2.5),
        camera_lookat=(0.0, 0.0, 1.0),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.2),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Sphere(pos=(0.0, 0.0, 2.0), radius=0.2),
    material=gs.materials.Rigid(rho=500, friction=0.4, restitution=0.5),
    surface=gs.surfaces.Default(color=(0.2, 0.5, 0.9, 1.0)),
)

scene.add_force_field(
    gs.options.ForceField(
        type="constant",
        direction=(1.0, 0.0, 0.0),
        strength=8.0,
    )
)

scene.build()

for _ in range(500):
    scene.step()
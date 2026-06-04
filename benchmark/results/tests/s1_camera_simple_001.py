"""
User Query: Set up a scene with a falling sphere and render it from a top-down view.
task_id: s1_camera_simple_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, -3.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.8),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.2),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Sphere(pos=(0.0, 0.0, 1.5), radius=0.2),
    material=gs.materials.Rigid(rho=500, friction=0.4, restitution=0.6),
    surface=gs.surfaces.Default(color=(0.9, 0.2, 0.2, 1.0)),
)

scene.add_camera(
    pos=(0.0, 0.0, 4.0),
    lookat=(0.0, 0.0, 0.0),
    up=(0.0, 1.0, 0.0),
    res=(640, 480),
)

scene.build()

for _ in range(300):
    scene.step()
"""
User Query: Create a sphere and change its color to bright red.
task_id: s1_surface_simple_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, 2.0, 1.8),
        camera_lookat=(0.0, 0.0, 0.5),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.2),
    surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Sphere(pos=(0.0, 0.0, 0.5), radius=0.5),
    material=gs.materials.Rigid(rho=1000, friction=0.5, restitution=0.6),
    surface=gs.surfaces.Default(color=(1.0, 0.0, 0.0, 1.0)),
)

scene.build()

for _ in range(300):
    scene.step()
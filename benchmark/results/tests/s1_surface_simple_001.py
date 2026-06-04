"""
User Query: Create a blue sphere on the ground.
task_id: s1_surface_simple_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

scene.add_entity(
    gs.morphs.Sphere(pos=(0.0, 0.0, 0.5), radius=0.5),
    material=gs.materials.Rigid(rho=1000, friction=0.5, restitution=0.2),
    surface=gs.surfaces.Default(color=(0.0, 0.0, 1.0, 1.0)),
)

scene.build()

for _ in range(240):
    scene.step()
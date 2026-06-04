"""
User Query: Place a shiny metallic sphere on the ground with a reflective silver appearance.
task_id: s1_surface_simple_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    renderer=gs.options.renderers.RayTracer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

scene.add_entity(
    gs.morphs.Sphere(pos=(0.0, 0.0, 0.5), radius=0.5),
    material=gs.materials.Rigid(rho=7800, friction=0.4, restitution=0.2),
    surface=gs.surfaces.Aluminium(color=(0.9, 0.9, 0.9, 1.0)),
)

scene.build()

for _ in range(240):
    scene.step()
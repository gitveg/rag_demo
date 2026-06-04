"""
User Query: Place a red metallic sphere and a yellow matte box next to each other on a gray ground plane. Both should have smooth, realistic-looking surfaces.
task_id: s1_surface_medium_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    show_viewer=True,
    renderer=gs.options.renderers.RayTracer(),
)

scene.add_entity(
    gs.Entity(
        morph=gs.morphs.Plane(),
        surface=gs.surfaces.Rough(color=(0.5, 0.5, 0.5, 1.0)),
    )
)

scene.add_entity(
    gs.Entity(
        morph=gs.morphs.Sphere(pos=(-0.6, 0.0, 0.5), radius=0.5),
        material=gs.materials.Rigid(rho=7800, friction=0.4, restitution=0.2),
        surface=gs.surfaces.Iron(color=(0.9, 0.1, 0.1, 1.0)),
    )
)

scene.add_entity(
    gs.Entity(
        morph=gs.morphs.Box(pos=(0.6, 0.0, 0.5), size=(0.8, 0.8, 0.8)),
        material=gs.materials.Rigid(rho=800, friction=0.6, restitution=0.1),
        surface=gs.surfaces.Rough(color=(1.0, 0.85, 0.1, 1.0)),
    )
)

scene.build()

for _ in range(1000):
    scene.step()
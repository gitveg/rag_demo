"""
User Query: Create a wind-like force pushing horizontally across the scene, affecting a group of small light cubes scattered on the floor.
task_id: s1_force_field_medium_003
"""

import genesis as gs
import random

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(6.0, -8.0, 5.0),
        camera_lookat=(0.0, 0.0, 0.8),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=2000, friction=0.8, restitution=0.1),
    surface=gs.surfaces.Rough(color=(0.5, 0.5, 0.5, 1.0)),
)

random.seed(42)
for _ in range(24):
    x = random.uniform(-2.5, 2.5)
    y = random.uniform(-2.5, 2.5)
    size_xy = random.uniform(0.12, 0.2)
    height = random.uniform(0.12, 0.2)
    scene.add_entity(
        gs.morphs.Box(
            pos=(x, y, height * 0.5 + 0.01),
            size=(size_xy, size_xy, height),
        ),
        material=gs.materials.Rigid(rho=120, friction=0.35, restitution=0.15),
        surface=gs.surfaces.Default(
            color=(
                random.uniform(0.2, 0.9),
                random.uniform(0.2, 0.9),
                random.uniform(0.2, 0.9),
                1.0,
            )
        ),
    )

scene.add_force_field(
    gs.options.ForceField(
        type="constant",
        direction=(1.0, 0.0, 0.0),
        strength=18.0,
    )
)

scene.build()

for _ in range(1200):
    scene.step()
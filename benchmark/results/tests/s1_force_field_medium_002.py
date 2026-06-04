"""
User Query: Place several boxes on the ground and apply a pulsing upward force field that periodically lifts the lighter boxes into the air.
task_id: s1_force_field_medium_002
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(6.0, -8.0, 5.5),
        camera_lookat=(0.0, 0.0, 1.0),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.1),
    surface=gs.surfaces.Rough(color=(0.35, 0.35, 0.35, 1.0)),
)

box_positions = [
    (-2.0, 0.0, 0.3),
    (-1.0, 0.0, 0.3),
    (0.0, 0.0, 0.3),
    (1.0, 0.0, 0.3),
    (2.0, 0.0, 0.3),
]

densities = [120, 220, 400, 700, 1200]
colors = [
    (0.95, 0.35, 0.35, 1.0),
    (0.95, 0.55, 0.25, 1.0),
    (0.95, 0.85, 0.25, 1.0),
    (0.35, 0.75, 0.95, 1.0),
    (0.55, 0.45, 0.95, 1.0),
]

for pos, rho, color in zip(box_positions, densities, colors):
    scene.add_entity(
        morph=gs.morphs.Box(pos=pos, size=(0.5, 0.5, 0.5)),
        material=gs.materials.Rigid(rho=rho, friction=0.6, restitution=0.15),
        surface=gs.surfaces.Default(color=color),
    )

upward_field = scene.add_force_field(
    gs.options.ForceField(type="constant", direction=(0.0, 0.0, 1.0), strength=0.0)
)

scene.build()

total_steps = 1200
base_strength = 18.0
pulse_amplitude = 32.0
pulse_frequency = 0.75

for step in range(total_steps):
    t = step * 0.01
    pulse = 0.5 * (1.0 + math.sin(2.0 * math.pi * pulse_frequency * t))
    strength = base_strength + pulse_amplitude * pulse
    upward_field.strength = strength
    scene.step()
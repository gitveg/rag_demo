"""
User Query: Create three cubes side by side with different surface appearances: matte red plastic, rough concrete, and polished gold metal.
task_id: s1_surface_medium_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    surface=gs.surfaces.Rough(color=(0.85, 0.85, 0.85, 1.0)),
)

cube_size = (0.6, 0.6, 0.6)
z = cube_size[2] / 2

scene.add_entity(
    gs.morphs.Box(pos=(-1.0, 0.0, z), size=cube_size),
    material=gs.materials.Rigid(rho=1200, friction=0.6, restitution=0.1),
    surface=gs.surfaces.Default(color=(0.85, 0.15, 0.15, 1.0)),
)

scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, z), size=cube_size),
    material=gs.materials.Rigid(rho=2400, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Rough(color=(0.55, 0.55, 0.55, 1.0)),
)

scene.add_entity(
    gs.morphs.Box(pos=(1.0, 0.0, z), size=cube_size),
    material=gs.materials.Rigid(rho=19300, friction=0.3, restitution=0.05),
    surface=gs.surfaces.Gold(color=(1.0, 0.84, 0.0, 1.0)),
)

scene.add_camera(
    pos=(3.5, -4.0, 2.2),
    lookat=(0.0, 0.0, 0.4),
    res=(1280, 720),
)

scene.build()

for _ in range(240):
    scene.step()
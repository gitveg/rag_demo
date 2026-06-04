"""
User Query: Spawn a cube and a cylinder. Give the cube a shiny metallic silver finish and make the cylinder a matte blue plastic.
task_id: s1_surface_medium_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, -3.0, 2.0),
        camera_lookat=(0.0, 0.0, 0.6),
    ),
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    surface=gs.surfaces.Default(color=(0.9, 0.9, 0.9, 1.0)),
)

scene.add_entity(
    gs.morphs.Box(pos=(-0.6, 0.0, 0.5), size=(0.6, 0.6, 0.6)),
    material=gs.materials.Rigid(rho=7800, friction=0.4, restitution=0.1),
    surface=gs.surfaces.Aluminium(color=(0.9, 0.9, 0.95, 1.0)),
)

scene.add_entity(
    gs.morphs.Cylinder(pos=(0.7, 0.0, 0.5), radius=0.25, height=1.0),
    material=gs.materials.Rigid(rho=1200, friction=0.7, restitution=0.05),
    surface=gs.surfaces.Rough(color=(0.1, 0.3, 0.9, 1.0)),
)

scene.build()

for _ in range(300):
    scene.step()
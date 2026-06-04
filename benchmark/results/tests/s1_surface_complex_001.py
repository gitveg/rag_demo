"""
User Query: Load a robot arm from an MJCF file and give it a polished metallic appearance. Place a translucent red box on the ground in front of it with a slightly rough surface texture.
task_id: s1_surface_complex_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.8, -2.2, 1.8),
        camera_lookat=(0.6, 0.0, 0.6),
    ),
    sim_options=gs.options.SimOptions(
        dt=0.01,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.1),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.MJCF(
        file="xml/franka_emika_panda/panda.xml",
        pos=(0.0, 0.0, 0.0),
    ),
    surface=gs.surfaces.Aluminium(color=(0.9, 0.92, 0.95, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.75, 0.0, 0.15),
        size=(0.25, 0.25, 0.25),
    ),
    material=gs.materials.Rigid(rho=500, friction=0.6, restitution=0.05),
    surface=gs.surfaces.Glass(color=(1.0, 0.1, 0.1, 0.5)),
)

scene.build()

for _ in range(500):
    scene.step()
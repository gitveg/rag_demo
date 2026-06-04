"""
User Query: Position a camera at a 45-degree angle above the scene and record a 5-second video of a ball bouncing.
task_id: s1_camera_medium_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(friction=0.8, coup_friction=0.1, coup_restitution=0.9),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

scene.add_entity(
    gs.morphs.Sphere(pos=(0.0, 0.0, 1.5), radius=0.15),
    material=gs.materials.Rigid(rho=200.0, friction=0.4, coup_friction=0.1, coup_restitution=0.9),
    surface=gs.surfaces.Rough(color=(0.9, 0.2, 0.2, 1.0)),
)

camera = scene.add_camera(
    pos=(2.5, 2.5, 2.5),
    lookat=(0.0, 0.0, 0.6),
    res=(1280, 720),
    fov=50,
)

scene.start_recording()

scene.build()

steps = int(5.0 / 0.01)
for _ in range(steps):
    scene.step()

scene.stop_recording(save_to_filename="bouncing_ball_5s.mp4")
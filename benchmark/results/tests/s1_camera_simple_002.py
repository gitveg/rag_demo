"""
User Query: Record a video of a rigid ball falling onto the ground from a fixed side view camera.
task_id: s1_camera_simple_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, -4.0, 2.0),
        camera_lookat=(0.0, 0.0, 0.8),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.2),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

scene.add_entity(
    gs.morphs.Sphere(pos=(0.0, 0.0, 2.0), radius=0.2),
    material=gs.materials.Rigid(rho=1200, friction=0.4, restitution=0.6),
    surface=gs.surfaces.Default(color=(0.9, 0.2, 0.2, 1.0)),
)

camera = scene.add_camera(
    pos=(3.0, -4.0, 1.5),
    lookat=(0.0, 0.0, 0.6),
    res=(1280, 720),
    fov=45,
)

scene.build()
scene.start_recording()

for _ in range(240):
    scene.step()

camera.stop_recording(save_to_filename="s1_camera_simple_002.mp4")
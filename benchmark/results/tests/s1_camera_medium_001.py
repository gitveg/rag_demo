"""
User Query: Create a scene with a red sphere falling onto a plane. Add a camera looking at the sphere from a 45-degree angle and record the simulation as a video.
task_id: s1_camera_medium_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, 3.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.8),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

plane = scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.2),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

sphere = scene.add_entity(
    morph=gs.morphs.Sphere(pos=(0.0, 0.0, 1.5), radius=0.2),
    material=gs.materials.Rigid(rho=1000, friction=0.4, restitution=0.6),
    surface=gs.surfaces.Default(color=(1.0, 0.0, 0.0, 1.0)),
)

camera = scene.add_camera(
    pos=(2.5, 2.5, 2.0),
    lookat=(0.0, 0.0, 1.0),
    res=(1280, 720),
    fov=50,
)

scene.build()
scene.start_recording()

for _ in range(240):
    scene.step()

scene.stop_recording(save_to_filename="red_sphere_fall.mp4")
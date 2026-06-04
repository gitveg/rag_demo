"""
User Query: Create a cinematic recording where the camera slowly orbits around a central object while it is being deformed, capturing the action from all sides at 60 frames per second.
task_id: s1_camera_complex_003
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=1.0 / 240.0),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(4.0, 2.5, 2.0),
        camera_lookat=(0.0, 0.0, 0.8),
    ),
    rigid_options=gs.options.RigidOptions(
        gravity=(0.0, 0.0, -9.81),
    ),
    fem_options=gs.options.FEMOptions(),
    renderer=gs.options.renderers.RayTracer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Rough(color=(0.18, 0.18, 0.2, 1.0)),
)

deformable = scene.add_entity(
    gs.morphs.Sphere(pos=(0.0, 0.0, 0.9), radius=0.35),
    material=gs.materials.FEM.Elastic(rho=1000.0, E=8e4, nu=0.22, model="linear"),
    surface=gs.surfaces.Glass(color=(0.35, 0.7, 1.0, 0.5)),
)

press_top = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 1.55), size=(0.9, 0.9, 0.18)),
    material=gs.materials.Rigid(rho=500.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

press_bottom = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 0.22), size=(1.0, 1.0, 0.16)),
    material=gs.materials.Rigid(rho=500.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Aluminium(color=(0.9, 0.9, 0.9, 1.0)),
)

cam = scene.add_camera(
    res=(1280, 720),
    pos=(3.2, 0.0, 1.5),
    lookat=(0.0, 0.0, 0.8),
    fov=50,
)

scene.start_recording(fps=60)
scene.build()

sim_fps = 240
record_fps = 60
steps_per_frame = sim_fps // record_fps
total_frames = 480
total_steps = total_frames * steps_per_frame

orbit_radius = 3.2
base_height = 1.55
lookat = (0.0, 0.0, 0.78)

start_top_z = 1.55
min_top_z = 0.86

for step in range(total_steps):
    t = step / float(total_steps - 1)

    angle = 2.0 * math.pi * t
    cam_x = orbit_radius * math.cos(angle)
    cam_y = orbit_radius * math.sin(angle)
    cam_z = base_height + 0.12 * math.sin(2.0 * angle)
    cam.set_pose(pos=(cam_x, cam_y, cam_z), lookat=lookat)

    if t < 0.28:
        top_z = start_top_z - (start_top_z - min_top_z) * (t / 0.28)
    elif t < 0.72:
        top_z = min_top_z
    else:
        top_z = min_top_z + (start_top_z - min_top_z) * ((t - 0.72) / 0.28)

    press_top.set_pos((0.0, 0.0, top_z))

    scene.step()

scene.stop_recording(save_to_filename="s1_camera_complex_003.mp4")
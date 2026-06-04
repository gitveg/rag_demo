"""
User Query: Load a humanoid robot (use gs.morphs.MJCF(file="xml/humanoid.xml")) in a room with boxes. Create a moving camera that orbits around the robot while recording, plus a fixed overhead camera capturing the whole scene.
task_id: s1_camera_complex_002
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(4.0, -4.0, 2.5),
        camera_lookat=(0.0, 0.0, 1.0),
        camera_fov=50,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.88, 1.0)),
)

wall_material = gs.materials.Rigid(rho=400.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0)
wall_surface = gs.surfaces.Rough(color=(0.92, 0.92, 0.95, 1.0))
box_material = gs.materials.Rigid(rho=300.0, friction=0.9, coup_friction=0.1, coup_restitution=0.0)

scene.add_entity(
    gs.morphs.Box(pos=(0.0, -4.0, 1.5), size=(8.0, 0.2, 3.0)),
    material=wall_material,
    surface=wall_surface,
)
scene.add_entity(
    gs.morphs.Box(pos=(0.0, 4.0, 1.5), size=(8.0, 0.2, 3.0)),
    material=wall_material,
    surface=wall_surface,
)
scene.add_entity(
    gs.morphs.Box(pos=(-4.0, 0.0, 1.5), size=(0.2, 8.0, 3.0)),
    material=wall_material,
    surface=wall_surface,
)
scene.add_entity(
    gs.morphs.Box(pos=(4.0, 0.0, 1.5), size=(0.2, 8.0, 3.0)),
    material=wall_material,
    surface=wall_surface,
)

scene.add_entity(
    gs.morphs.Box(pos=(-1.5, 1.2, 0.3), size=(0.6, 0.6, 0.6)),
    material=box_material,
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(1.4, -1.0, 0.4), size=(0.8, 0.5, 0.8)),
    material=box_material,
    surface=gs.surfaces.Gold(color=(1.0, 0.84, 0.0, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(1.8, 1.5, 0.25), size=(0.5, 0.5, 0.5)),
    material=box_material,
    surface=gs.surfaces.Aluminium(color=(0.9, 0.9, 0.9, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(-1.8, -1.6, 0.5), size=(0.7, 0.7, 1.0)),
    material=box_material,
    surface=gs.surfaces.Default(color=(0.4, 0.7, 0.9, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(0.0, 2.2, 0.35), size=(1.0, 0.6, 0.7)),
    material=box_material,
    surface=gs.surfaces.Default(color=(0.9, 0.5, 0.4, 1.0)),
)

humanoid = scene.add_entity(
    gs.morphs.MJCF(file="xml/humanoid.xml", pos=(0.0, 0.0, 1.35)),
)

orbit_cam = scene.add_camera(
    res=(1280, 720),
    pos=(3.5, 0.0, 1.8),
    lookat=(0.0, 0.0, 1.0),
    fov=55,
)
overhead_cam = scene.add_camera(
    res=(1280, 720),
    pos=(0.0, 0.0, 8.5),
    lookat=(0.0, 0.0, 0.8),
    fov=65,
)

scene.start_recording()

scene.build()

num_steps = 600
orbit_radius = 3.5
orbit_height = 1.8
lookat_height = 1.0

for i in range(num_steps):
    theta = 2.0 * math.pi * i / num_steps
    cam_x = orbit_radius * math.cos(theta)
    cam_y = orbit_radius * math.sin(theta)
    orbit_cam.set_pose(
        pos=(cam_x, cam_y, orbit_height),
        lookat=(0.0, 0.0, lookat_height),
    )
    scene.step()

scene.stop_recording(save_to_filename="s1_camera_complex_002.mp4")
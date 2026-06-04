"""
User Query: Place a mobile robot in a room with obstacles and simulate a lidar sensor scanning the environment while the robot moves forward.
task_id: s1_sensor_medium_002
"""

import genesis as gs
import math

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(6.0, -6.0, 4.0),
        camera_lookat=(0.0, 0.0, 0.8),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(friction=1.0),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

wall_thickness = 0.2
wall_height = 1.2
room_half_x = 4.0
room_half_y = 4.0

# Room walls
scene.add_entity(
    gs.morphs.Box(pos=(0.0, room_half_y, wall_height / 2), size=(2 * room_half_x + wall_thickness, wall_thickness, wall_height)),
    material=gs.materials.Rigid(friction=0.8),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.75, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(0.0, -room_half_y, wall_height / 2), size=(2 * room_half_x + wall_thickness, wall_thickness, wall_height)),
    material=gs.materials.Rigid(friction=0.8),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.75, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(room_half_x, 0.0, wall_height / 2), size=(wall_thickness, 2 * room_half_y + wall_thickness, wall_height)),
    material=gs.materials.Rigid(friction=0.8),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.75, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(-room_half_x, 0.0, wall_height / 2), size=(wall_thickness, 2 * room_half_y + wall_thickness, wall_height)),
    material=gs.materials.Rigid(friction=0.8),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.75, 1.0)),
)

# Obstacles
obstacles = [
    gs.morphs.Box(pos=(0.8, 0.6, 0.35), size=(0.8, 0.8, 0.7)),
    gs.morphs.Box(pos=(2.0, -1.0, 0.5), size=(0.6, 1.2, 1.0)),
    gs.morphs.Cylinder(pos=(1.6, 1.8, 0.45), radius=0.35, height=0.9),
    gs.morphs.Box(pos=(-1.2, 1.2, 0.3), size=(1.0, 0.5, 0.6)),
    gs.morphs.Cylinder(pos=(-2.0, -1.5, 0.4), radius=0.3, height=0.8),
]
for obs in obstacles:
    scene.add_entity(
        obs,
        material=gs.materials.Rigid(friction=0.9),
        surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
    )

# Mobile robot body
robot = scene.add_entity(
    gs.morphs.Cylinder(pos=(-3.0, 0.0, 0.2), radius=0.22, height=0.4),
    material=gs.materials.Rigid(rho=200.0, friction=1.2),
    surface=gs.surfaces.Aluminium(color=(0.85, 0.85, 0.9, 1.0)),
)

# Lidar sensor attached to robot
pattern = gs.sensors.SphericalPattern(fov=(360.0, 20.0), n_points=(360, 8))
lidar_opts = gs.sensors.Lidar(
    pattern=pattern,
    entity_idx=robot.idx,
    link_idx_local=0,
    pos_offset=(0.0, 0.0, 0.25),
)
lidar = scene.add_sensor(lidar_opts)

scene.build()

robot_speed = 0.6
n_steps = 600

for step in range(n_steps):
    t = step * 0.01

    x = -3.0 + robot_speed * t
    y = 0.15 * math.sin(0.8 * t)
    z = 0.2

    if x > 3.0:
        x = 3.0

    robot.set_pos((x, y, z))

    scene.step()

    scan = lidar.read()
    if step % 60 == 0:
        min_dist = float(scan.distances.min()) if len(scan.distances) > 0 else float("nan")
        print(f"step={step:04d}, robot_pos=({x:.2f}, {y:.2f}, {z:.2f}), lidar_points={len(scan.distances)}, min_distance={min_dist:.3f}")
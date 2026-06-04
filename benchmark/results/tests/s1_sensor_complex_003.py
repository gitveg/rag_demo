"""
User Query: Mount a Lidar sensor on top of a moving platform and visualize the point cloud data as it scans a room containing various obstacles.
task_id: s1_sensor_complex_003
"""

import math
import numpy as np
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(8.0, -8.0, 6.0),
        camera_lookat=(0.0, 0.0, 1.0),
        camera_fov=50,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(friction=0.8),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

wall_thickness = 0.2
wall_height = 2.5
room_half_x = 4.0
room_half_y = 4.0

scene.add_entity(
    gs.morphs.Box(pos=(0.0, room_half_y + wall_thickness * 0.5, wall_height * 0.5), size=(2 * room_half_x + 2 * wall_thickness, wall_thickness, wall_height)),
    material=gs.materials.Rigid(friction=0.7),
    surface=gs.surfaces.Rough(color=(0.75, 0.78, 0.82, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(0.0, -room_half_y - wall_thickness * 0.5, wall_height * 0.5), size=(2 * room_half_x + 2 * wall_thickness, wall_thickness, wall_height)),
    material=gs.materials.Rigid(friction=0.7),
    surface=gs.surfaces.Rough(color=(0.75, 0.78, 0.82, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(room_half_x + wall_thickness * 0.5, 0.0, wall_height * 0.5), size=(wall_thickness, 2 * room_half_y, wall_height)),
    material=gs.materials.Rigid(friction=0.7),
    surface=gs.surfaces.Rough(color=(0.75, 0.78, 0.82, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(-room_half_x - wall_thickness * 0.5, 0.0, wall_height * 0.5), size=(wall_thickness, 2 * room_half_y, wall_height)),
    material=gs.materials.Rigid(friction=0.7),
    surface=gs.surfaces.Rough(color=(0.75, 0.78, 0.82, 1.0)),
)

obstacles = [
    gs.morphs.Box(pos=(-1.8, -1.2, 0.5), size=(0.8, 0.8, 1.0)),
    gs.morphs.Box(pos=(1.5, -0.5, 0.75), size=(1.2, 0.6, 1.5)),
    gs.morphs.Box(pos=(0.5, 2.0, 0.4), size=(0.7, 1.4, 0.8)),
    gs.morphs.Cylinder(pos=(-2.2, 1.8, 0.7), radius=0.35, height=1.4),
    gs.morphs.Cylinder(pos=(2.4, 1.4, 0.6), radius=0.25, height=1.2),
    gs.morphs.Sphere(pos=(0.0, -2.2, 0.5), radius=0.5),
]

obstacle_colors = [
    (0.85, 0.30, 0.30, 1.0),
    (0.30, 0.70, 0.35, 1.0),
    (0.25, 0.50, 0.90, 1.0),
    (0.90, 0.75, 0.20, 1.0),
    (0.70, 0.40, 0.85, 1.0),
    (0.20, 0.75, 0.75, 1.0),
]

for morph, color in zip(obstacles, obstacle_colors):
    scene.add_entity(
        morph,
        material=gs.materials.Rigid(friction=0.6),
        surface=gs.surfaces.Default(color=color),
    )

platform = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 0.2), size=(0.8, 0.6, 0.4)),
    material=gs.materials.Rigid(friction=0.9),
    surface=gs.surfaces.Iron(color=(0.35, 0.38, 0.45, 1.0)),
)

lidar_pattern = gs.sensors.SphericalPattern(fov=(360.0, 45.0), n_points=(720, 32))
lidar_opts = gs.sensors.Lidar(
    pattern=lidar_pattern,
    entity_idx=platform.idx,
    link_idx_local=0,
    pos_offset=(0.0, 0.0, 0.45),
)
lidar = scene.add_sensor(lidar_opts)

scene.build()

dt = 0.01
num_steps = 1200

trajectory_radius = 2.2
angular_speed = 0.35
platform_height = 0.2

last_points = None

for step in range(num_steps):
    t = step * dt

    target_x = trajectory_radius * math.cos(angular_speed * t)
    target_y = trajectory_radius * math.sin(angular_speed * t)
    target_z = platform_height

    if hasattr(platform, "set_pos"):
        platform.set_pos((target_x, target_y, target_z))

    if hasattr(platform, "set_quat"):
        yaw = angular_speed * t + math.pi * 0.5
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        platform.set_quat((0.0, 0.0, sy, cy))

    scene.step()

    if step % 20 == 0:
        data = lidar.read()
        points = np.array(data.points)
        last_points = points

        print(f"step={step:04d}  lidar_points={points.shape[0]}")
        if points.shape[0] > 0:
            mins = points.min(axis=0)
            maxs = points.max(axis=0)
            print(
                "point_cloud_bounds "
                f"x[{mins[0]: .2f}, {maxs[0]: .2f}] "
                f"y[{mins[1]: .2f}, {maxs[1]: .2f}] "
                f"z[{mins[2]: .2f}, {maxs[2]: .2f}]"
            )

if last_points is not None:
    try:
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(8, 7))
        ax = fig.add_subplot(111, projection="3d")
        stride = max(1, last_points.shape[0] // 5000)
        sampled = last_points[::stride]
        ax.scatter(sampled[:, 0], sampled[:, 1], sampled[:, 2], s=1, c=sampled[:, 2], cmap="viridis")
        ax.set_title("Lidar Point Cloud Snapshot")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_xlim(-5, 5)
        ax.set_ylim(-5, 5)
        ax.set_zlim(0, 3)
        plt.tight_layout()
        plt.savefig("lidar_point_cloud_snapshot.png", dpi=200)
        print("Saved point cloud visualization to lidar_point_cloud_snapshot.png")
    except Exception as e:
        print(f"Visualization skipped: {e}")
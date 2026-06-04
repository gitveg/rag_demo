"""
User Query: Load a Franka Panda robot arm on a mobile base (use gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml")). Attach a Lidar sensor and a forward-facing depth camera to it. Move the robot through a room with obstacles and record synchronized sensor data.
task_id: s1_sensor_complex_002
"""

import genesis as gs
import math
import os
import numpy as np

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(6.0, -4.0, 3.5),
        camera_lookat=(1.5, 0.0, 1.0),
        camera_fov=50,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

ground = scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

room_thickness = 0.1
room_height = 2.2
room_size_x = 8.0
room_size_y = 6.0

walls = []
walls.append(
    scene.add_entity(
        morph=gs.morphs.Box(pos=(room_size_x / 2, 0.0, room_height / 2), size=(room_thickness, room_size_y, room_height)),
        material=gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0),
        surface=gs.surfaces.Rough(color=(0.92, 0.92, 0.95, 1.0)),
    )
)
walls.append(
    scene.add_entity(
        morph=gs.morphs.Box(pos=(-room_size_x / 2, 0.0, room_height / 2), size=(room_thickness, room_size_y, room_height)),
        material=gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0),
        surface=gs.surfaces.Rough(color=(0.92, 0.92, 0.95, 1.0)),
    )
)
walls.append(
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, room_size_y / 2, room_height / 2), size=(room_size_x, room_thickness, room_height)),
        material=gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0),
        surface=gs.surfaces.Rough(color=(0.90, 0.90, 0.93, 1.0)),
    )
)
walls.append(
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, -room_size_y / 2, room_height / 2), size=(room_size_x, room_thickness, room_height)),
        material=gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0),
        surface=gs.surfaces.Rough(color=(0.90, 0.90, 0.93, 1.0)),
    )
)

obstacle_specs = [
    ((1.2, -0.6, 0.35), (0.6, 0.6, 0.7), (0.8, 0.2, 0.2, 1.0)),
    ((2.3, 1.0, 0.50), (0.4, 1.2, 1.0), (0.2, 0.4, 0.8, 1.0)),
    ((-0.5, 1.3, 0.40), (0.8, 0.5, 0.8), (0.2, 0.7, 0.3, 1.0)),
    ((-1.7, -1.0, 0.30), (0.5, 0.5, 0.6), (0.7, 0.6, 0.2, 1.0)),
    ((0.2, -1.8, 0.60), (1.0, 0.4, 1.2), (0.5, 0.3, 0.7, 1.0)),
]
for pos, size, color in obstacle_specs:
    scene.add_entity(
        morph=gs.morphs.Box(pos=pos, size=size),
        material=gs.materials.Rigid(rho=200.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
        surface=gs.surfaces.Default(color=color),
    )

mobile_base = scene.add_entity(
    morph=gs.morphs.Box(pos=(-2.7, -2.1, 0.15), size=(0.7, 0.5, 0.3)),
    material=gs.materials.Rigid(rho=250.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Iron(color=(0.35, 0.38, 0.42, 1.0)),
)

robot = scene.add_entity(
    morph=gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml", pos=(-2.7, -2.1, 0.30)),
)

lidar_pattern = gs.sensors.SphericalPattern(
    fov=(360.0, 30.0),
    n_points=(360, 16),
)
lidar_opts = gs.sensors.Lidar(
    pattern=lidar_pattern,
    entity_idx=robot.idx,
    link_idx_local=0,
    pos_offset=(0.0, 0.0, 0.45),
)
lidar = scene.add_sensor(lidar_opts)

depth_pattern = gs.sensors.DepthCameraPattern(
    res=(320, 240),
    fov_horizontal=70.0,
)
depth_opts = gs.sensors.DepthCamera(
    pattern=depth_pattern,
    entity_idx=robot.idx,
    link_idx_local=0,
    pos_offset=(0.18, 0.0, 0.42),
)
depth_cam = scene.add_sensor(depth_opts)

cam = scene.add_camera(
    res=(1280, 720),
    pos=(5.5, -4.0, 3.2),
    lookat=(0.0, 0.0, 0.8),
    fov=50,
)

scene.start_recording()
scene.build()

out_dir = "sensor_sync_output_s1_sensor_complex_002"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(os.path.join(out_dir, "depth_images"), exist_ok=True)

trajectory = [
    (-2.7, -2.1, 0.0),
    (-1.8, -1.6, 0.0),
    (-0.8, -1.2, 0.0),
    (0.2, -0.8, 0.0),
    (1.0, -0.2, 0.0),
    (1.6, 0.7, 0.0),
    (1.2, 1.5, 0.0),
    (0.1, 1.9, 0.0),
    (-1.0, 1.6, 0.0),
    (-1.8, 0.8, 0.0),
]

steps_per_segment = 80
total_steps = steps_per_segment * (len(trajectory) - 1)

metadata = []

def interpolate_path(path, seg_idx, alpha):
    p0 = np.array(path[seg_idx], dtype=float)
    p1 = np.array(path[seg_idx + 1], dtype=float)
    return (1.0 - alpha) * p0 + alpha * p1

for step in range(total_steps):
    seg_idx = min(step // steps_per_segment, len(trajectory) - 2)
    local_step = step % steps_per_segment
    alpha = local_step / float(steps_per_segment)

    pos = interpolate_path(trajectory, seg_idx, alpha)
    next_alpha = min((local_step + 1) / float(steps_per_segment), 1.0)
    pos_next = interpolate_path(trajectory, seg_idx, next_alpha)
    direction = pos_next[:2] - pos[:2]
    yaw = math.atan2(direction[1], direction[0] + 1e-12)

    mobile_base.set_pos((float(pos[0]), float(pos[1]), 0.15))
    mobile_base.set_quat(gs.utils.geom.xyz_to_quat((0.0, 0.0, yaw)))

    robot.set_pos((float(pos[0]), float(pos[1]), 0.30))
    robot.set_quat(gs.utils.geom.xyz_to_quat((0.0, 0.0, yaw)))

    scene.step()

    lidar_data = lidar.read()
    depth_data = depth_cam.read()
    depth_img = depth_cam.read_image()

    if hasattr(depth_img, "detach"):
        depth_img_np = depth_img.detach().cpu().numpy()
    elif hasattr(depth_img, "cpu"):
        depth_img_np = depth_img.cpu().numpy()
    else:
        depth_img_np = np.array(depth_img)

    lidar_points = lidar_data.points
    lidar_distances = lidar_data.distances
    depth_points = depth_data.points
    depth_distances = depth_data.distances

    if hasattr(lidar_points, "detach"):
        lidar_points_np = lidar_points.detach().cpu().numpy()
        lidar_distances_np = lidar_distances.detach().cpu().numpy()
    else:
        lidar_points_np = np.array(lidar_points)
        lidar_distances_np = np.array(lidar_distances)

    if hasattr(depth_points, "detach"):
        depth_points_np = depth_points.detach().cpu().numpy()
        depth_distances_np = depth_distances.detach().cpu().numpy()
    else:
        depth_points_np = np.array(depth_points)
        depth_distances_np = np.array(depth_distances)

    np.save(os.path.join(out_dir, f"lidar_points_{step:05d}.npy"), lidar_points_np)
    np.save(os.path.join(out_dir, f"lidar_distances_{step:05d}.npy"), lidar_distances_np)
    np.save(os.path.join(out_dir, f"depth_points_{step:05d}.npy"), depth_points_np)
    np.save(os.path.join(out_dir, f"depth_distances_{step:05d}.npy"), depth_distances_np)
    np.save(os.path.join(out_dir, "depth_images", f"depth_image_{step:05d}.npy"), depth_img_np)

    metadata.append(
        {
            "frame": step,
            "sim_time": step * 0.01,
            "base_pos_xyz": [float(pos[0]), float(pos[1]), 0.15],
            "robot_pos_xyz": [float(pos[0]), float(pos[1]), 0.30],
            "yaw_rad": float(yaw),
            "lidar_points_file": f"lidar_points_{step:05d}.npy",
            "lidar_distances_file": f"lidar_distances_{step:05d}.npy",
            "depth_points_file": f"depth_points_{step:05d}.npy",
            "depth_distances_file": f"depth_distances_{step:05d}.npy",
            "depth_image_file": os.path.join("depth_images", f"depth_image_{step:05d}.npy"),
        }
    )

cam.stop_recording(save_to_filename=os.path.join(out_dir, "room_navigation.mp4"))

with open(os.path.join(out_dir, "metadata.jsonl"), "w", encoding="utf-8") as f:
    for item in metadata:
        f.write(str(item) + "\n")

print(f"Saved synchronized sensor data and video to: {out_dir}")
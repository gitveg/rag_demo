import argparse
import os
import threading
import time
import numpy as np

import genesis as gs
from genesis.utils.geom import euler_to_quat

# No pynput, we'll drive autonomously

KEY_DPOS = 0.1
KEY_DANGLE = 0.1

MOVE_RADIUS = 1.0
MOVE_RATE = 1.0 / 100.0

NUM_CYLINDERS = 8
NUM_BOXES = 6
CYLINDER_RING_RADIUS = 3.0
BOX_RING_RADIUS = 5.0


def main():
    gs.init()

    # Create scene with viewer
    scene = gs.Scene(
        show_viewer=True,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -1, 1.5),
            camera_lookat=(0, 0, 0),
        ),
    )

    # Ground
    plane = scene.add_entity(
        morph=gs.morphs.Plane(),
    )

    # Obstacle cylinders
    for i in range(NUM_CYLINDERS):
        theta = 2 * np.pi * i / NUM_CYLINDERS
        x = CYLINDER_RING_RADIUS * np.cos(theta)
        y = CYLINDER_RING_RADIUS * np.sin(theta)
        scene.add_entity(
            morph=gs.morphs.Cylinder(
                pos=(x, y, 0.5),
                euler=(0, 0, 0),
                radius=0.2,
                height=1.0,
            ),
        )

    # Obstacle boxes
    for i in range(NUM_BOXES):
        theta = 2 * np.pi * i / NUM_BOXES
        x = BOX_RING_RADIUS * np.cos(theta)
        y = BOX_RING_RADIUS * np.sin(theta)
        scene.add_entity(
            morph=gs.morphs.Box(
                pos=(x, y, 0.5),
                euler=(0, 0, theta),
                size=(0.5, 0.5, 1.0),
            ),
        )

    # Vehicle model (URDF)
    # Replace 'vehicle.urdf' with your own URDF file
    car = scene.add_entity(
        morph=gs.morphs.URDF(
            file='vehicle.urdf',
            pos=(0, 0, 0.5),
            euler=(0, 0, 0),
        ),
    )

    # Sensors: LiDAR and DepthCamera (forward-facing)
    lidar = scene.add_sensor(
        sensor_options=gs.options.sensors.Lidar(
            pos=(0.0, 0.0, 0.3),  # on top of vehicle
            euler=(0, 0, 0),
            pattern=gs.options.sensors.SphericalPattern(
                fov=(360.0, 30.0),
                n_points=(64, 16),
            ),
        ),
    )

    forward_cam = scene.add_sensor(
        sensor_options=gs.options.sensors.DepthCamera(
            pos=(0.0, 0.2, 0.1),  # front of vehicle
            euler=(0, 0, 0),
            pattern=gs.options.sensors.DepthCameraPattern(
                res=(128, 96),
                fov_horizontal=90.0,
            ),
        ),
    )

    # Build scene
    scene.build(n_envs=1)

    # Get joint handles for driving (wheels)
    # Assumes URDF has wheel joints named 'left_wheel', 'right_wheel', etc.
    # Adjust according to your URDF
    left_joint = car.get_joint('left_wheel')
    right_joint = car.get_joint('right_wheel')
    joints = [left_joint, right_joint]

    # Set up PD gains for velocity control
    car.set_dofs_kp(np.full(len(joints), 10.0))
    car.set_dofs_kv(np.full(len(joints), 1.0))

    # Data recording lists
    lidar_pcds = []
    depth_images = []
    timestamps = []

    # Simulation loop
    for i in range(500):
        # Drive forward: set wheel velocities (rad/s)
        vel = 2.0  # rad/s
        target_positions = []
        for joint in joints:
            # Get current joint position
            current_pos = joint.get_dofs_position()
            # Command constant velocity
            target_positions.append(current_pos + vel * 0.01)

        car.control_dofs_position(target_positions, joints=joints)

        scene.step()

        # Read sensor data every 10 steps to reduce memory
        if i % 10 == 0:
            # LiDAR point cloud
            pcd = lidar.get_pcd()  # returns Nx3 array
            lidar_pcds.append(pcd)

            # Depth camera image
            depth = forward_cam.get_depth()  # returns HxW array
            depth_images.append(depth)

            timestamps.append(i * 0.01)  # assuming dt=0.01

    print("Recording finished. Data shapes:")
    print(f"  LiDAR point clouds: {len(lidar_pcds)} frames, each {lidar_pcds[0].shape}")
    print(f"  Depth images: {len(depth_images)} frames, each {depth_images[0].shape}")
    print(f"  Timestamps: {len(timestamps)} entries")

    # Optional: save data to numpy files
    np.savez('sensor_data.npz',
             lidar_pcds=np.array(lidar_pcds, dtype=object),
             depth_images=np.array(depth_images, dtype=object),
             timestamps=np.array(timestamps))


if __name__ == '__main__':
    main()
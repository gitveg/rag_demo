import numpy as np
from tqdm import tqdm

import genesis as gs


def main():
    # Initialize Genesis
    gs.init()

    # Create scene
    scene = gs.Scene(
        show_viewer=True,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, 2.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
    )

    # Add ground plane
    plane = scene.add_entity(
        morph=gs.morphs.Plane(),
    )

    # Add Franka robot arm
    robot = scene.add_entity(
        morph=gs.morphs.URDF(
            file="franka_emika_panda/panda.urdf",
            pos=(0.0, 0.0, 0.0),
            euler=(0.0, 0.0, 0.0),
        ),
    )

    # Build scene
    scene.build()

    # Attach IMU sensor to the end-effector link
    imu_opts = gs.options.sensors.IMU(
        entity=robot,
        link="panda_hand",
    )
    imu = scene.add_sensor(imu_opts)

    # Define a simple motion (e.g., move joint 0 and 1 sinusoidally)
    num_steps = 1000
    dt = 1e-2  # 100 Hz

    # Record data
    timestamps = []
    accelerations = []
    angular_velocities = []

    print("Running simulation and recording IMU data...")
    for t in tqdm(range(num_steps)):
        # Set joint positions for a smooth motion
        qpos = np.array([
            0.5 * np.sin(2 * np.pi * 0.1 * t * dt),
            0.3 * np.cos(2 * np.pi * 0.1 * t * dt),
            0.0,
            -0.7,
            0.0,
            0.7,
            0.0,
        ])
        robot.set_joints_qpos(qpos)

        # Step simulation
        scene.step()

        # Read IMU data
        imu_data = imu.read()
        accelerations.append(imu_data.acceleration)
        angular_velocities.append(imu_data.angular_velocity)
        timestamps.append(t * dt)

    # Print first few readings
    print("\nFirst 5 IMU readings:")
    for i in range(5):
        print(f"t={timestamps[i]:.3f}s: acc={accelerations[i]}, gyro={angular_velocities[i]}")

    print("Simulation finished.")


if __name__ == "__main__":
    main()
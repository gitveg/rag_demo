import numpy as np
import genesis as gs

def main():
    gs.init()

    # Create scene with a viewer
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -3, 2),
            camera_lookat=(0, 0, 1),
        ),
        show_viewer=True,
    )

    # Add ground plane
    plane = scene.add_entity(gs.options.morphs.Plane())

    # Add a falling sphere (rigid body)
    sphere = scene.add_entity(
        gs.options.morphs.Sphere(pos=(0, 0, 2.0), radius=0.3),
        material=gs.materials.Rigid(),
    )

    # Attach IMU sensor to the sphere’s base link
    imu_sensor = scene.add_sensor(
        gs.options.sensors.IMU(
            entity=sphere,
            link=sphere.get_link(0),
        )
    )

    scene.build()

    # Prepare storage and recording callback
    accelerations = []

    def my_data_func(scene, data_dict):
        # IMU.get_data() returns (accelerometer, gyroscope)
        accel = imu_sensor.get_data()[0]
        accelerations.append(accel.copy())
        return data_dict

    scene.start_recording(data_func=my_data_func)

    # Run simulation – the sphere falls, hits the plane, and may bounce
    for _ in range(500):
        scene.step()

    scene.stop_recording()

    # Save recorded linear acceleration to file
    accel_array = np.array(accelerations)
    np.save("imu_accelerations.npy", accel_array)
    print(f"Recorded IMU accelerations shape: {accel_array.shape}")

if __name__ == "__main__":
    main()
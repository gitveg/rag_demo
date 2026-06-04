import numpy as np
import genesis as gs

def main():
    gs.init()

    # Create scene with default options
    scene = gs.Scene()

    # Add a plane as the platform
    plane = scene.add_entity(gs.morphs.Plane())

    # Add a rigid box above the plane
    box = scene.add_entity(
        gs.morphs.Box(size=(0.1, 0.1, 0.1), pos=(0.0, 0.5, 0.0)),
        material=gs.materials.Rigid(),
    )

    # Add an IMU sensor attached to the box
    imu_sensor_opts = gs.options.sensors.IMU(
        attach_to=box,
    )
    scene.add_sensor(imu_sensor_opts)

    # Build the scene
    scene.build()

    # Record linear acceleration over time
    accelerations = []
    n_steps = 500  # 5 seconds at dt=0.01
    dt = 0.01

    for _ in range(n_steps):
        scene.step()
        # Retrieve IMU data: the sensor is stored in scene.sensors
        imu_data = scene.sensors[0].data
        acc = imu_data['linear_acceleration']
        accelerations.append(acc.copy())

    # Print some acceleration values around impact (when z acceleration changes)
    print("First 10 accelerations (x, y, z):")
    for i, acc in enumerate(accelerations[:10]):
        print(f"Step {i}: {acc}")

    # You can also analyze the data, e.g., detect impact
    # For simplicity, we just show that the simulation ran

if __name__ == "__main__":
    main()
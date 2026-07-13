import numpy as np
import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(show_viewer=True)

    # Ground plane
    scene.add_entity(gs.morphs.Plane())

    # Fixed pole (static tall box)
    pole = scene.add_entity(
        gs.morphs.Box(pos=(0.0, 0.0, 0.5), size=(0.1, 0.1, 1.0), fixed=True)
    )

    # Rotating rigid box
    box = scene.add_entity(
        gs.morphs.Box(pos=(1.5, 0.0, 0.15), size=(0.3, 0.3, 0.3))
    )

    # LiDAR sensor on top of pole, pointing at the box
    lidar = scene.add_sensor(
        gs.options.sensors.Lidar(
            pos=(0.0, 0.0, 1.1),     # top of the pole
            lookat=(1.5, 0.0, 0.15), # box center
        )
    )

    scene.build()

    # Start the box rotating around the vertical axis
    box.set_vel(ang_vel=[0.0, 0.0, 1.0])  # rad/s

    all_points = []  # collect point clouds per frame

    # Simulate and collect LiDAR data
    for step in range(500):
        scene.step()

        # Retrieve point cloud data from the LiDAR sensor
        if hasattr(lidar, "data"):
            pts = lidar.data  # typically an (N,3) numpy array
        else:
            pts = None

        if pts is not None and len(pts) > 0:
            all_points.append(pts)

    # Report captured data
    if all_points:
        print(f"Captured {len(all_points)} point clouds.")
        print(f"First frame shape: {all_points[0].shape}")
    else:
        print("No LiDAR data captured.")

if __name__ == "__main__":
    main()
import numpy as np
import genesis as gs

def main():
    gs.init()

    # Create scene
    scene = gs.Scene(
        show_viewer=True,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5.0, -5.0, 5.0),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        rigid_options=gs.options.RigidOptions(
            enable_collision=True,
        ),
    )

    # Ground plane
    plane = scene.add_entity(
        morph=gs.morphs.Plane(),
    )

    # Obstacles: cylinders and boxes in rings
    num_cylinders = 8
    num_boxes = 6
    cylinder_ring_radius = 3.0
    box_ring_radius = 5.0

    for i in range(num_cylinders):
        theta = 2 * np.pi * i / num_cylinders
        x = cylinder_ring_radius * np.cos(theta)
        y = cylinder_ring_radius * np.sin(theta)
        scene.add_entity(
            morph=gs.morphs.Cylinder(
                radius=0.3,
                height=1.0,
                pos=(x, y, 0.5),
            ),
        )

    for i in range(num_boxes):
        theta = 2 * np.pi * i / num_boxes + 0.2
        x = box_ring_radius * np.cos(theta)
        y = box_ring_radius * np.sin(theta)
        scene.add_entity(
            morph=gs.morphs.Box(
                size=(0.5, 0.5, 1.0),
                pos=(x, y, 0.5),
            ),
        )

    # Robot: a simple box on the ground
    robot = scene.add_entity(
        morph=gs.morphs.Box(
            size=(0.4, 0.4, 0.2),
            pos=(0.0, 0.0, 0.1),
            fixed=False,
        ),
        material=gs.materials.Rigid(
            rho=200.0,
        ),
    )

    # LiDAR sensor
    lidar = scene.add_sensor(
        sensor_options=gs.options.sensors.Lidar(
            pattern=gs.options.sensors.SphericalPattern(
                fov=(360.0, 30.0),
                n_points=(128, 32),
            ),
            max_range=10.0,
        ),
    )

    # Build scene
    scene.build()

    # Simulation loop
    n_steps = 500
    move_speed = 0.02  # forward speed along x

    for i in range(n_steps):
        # Move robot forward
        pos = robot.get_pos()
        new_pos = (pos[0] + move_speed, pos[1], pos[2])
        robot.set_pos(new_pos)

        # Update LiDAR pose (attach to robot, offset up)
        lidar_pose = np.array([new_pos[0], new_pos[1], new_pos[2] + 0.3, 0, 0, 0])
        lidar.set_pose(lidar_pose)

        # Read LiDAR data
        scan = lidar.get_scan()
        # distances = scan['distances']  # shape (n_rays,)
        # point_cloud = scan['point_cloud']  # shape (n_rays, 3)

        # Step simulation
        scene.step()

if __name__ == "__main__":
    main()
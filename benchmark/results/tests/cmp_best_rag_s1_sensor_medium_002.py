import numpy as np
import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        show_viewer=True,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.0, -5.0, 5.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
    )

    # Ground plane
    scene.add_entity(gs.morphs.Plane())

    # Mobile robot: a simple box base
    robot = scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 0.15),
            size=(0.5, 0.3, 0.15),
        )
    )

    # Cylinder obstacles in a ring
    num_cylinders = 8
    cylinder_radius = 3.0
    for i in range(num_cylinders):
        angle = i * 2 * np.pi / num_cylinders
        x = cylinder_radius * np.cos(angle)
        y = cylinder_radius * np.sin(angle)
        scene.add_entity(
            gs.morphs.Cylinder(
                pos=(x, y, 0.5),
                radius=0.15,
                height=1.0,
            )
        )

    # Box obstacles in a larger ring
    num_boxes = 6
    box_radius = 5.0
    for i in range(num_boxes):
        angle = i * 2 * np.pi / num_boxes
        x = box_radius * np.cos(angle)
        y = box_radius * np.sin(angle)
        scene.add_entity(
            gs.morphs.Box(
                pos=(x, y, 0.5),
                size=(0.3, 0.3, 0.5),
            )
        )

    # LiDAR sensor (will be moved on top of the robot manually)
    lidar = scene.add_sensor(gs.options.sensors.Lidar())

    scene.build()

    # Move the robot forward and keep the LiDAR attached above it
    for _ in range(1000):
        robot_pos = robot.get_pos()
        robot_quat = robot.get_quat()

        # Drive forward along the x-axis
        robot.set_pos(robot_pos + np.array([0.01, 0.0, 0.0]))
        robot.set_quat(robot_quat)  # maintain orientation

        # Move LiDAR to stay on top of the robot
        lidar.set_pose(pos=robot_pos + np.array([0.0, 0.0, 0.3]), quat=robot_quat)

        scene.step()

if __name__ == "__main__":
    main()
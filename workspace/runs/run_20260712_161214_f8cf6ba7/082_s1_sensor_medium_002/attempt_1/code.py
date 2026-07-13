import numpy as np
import genesis as gs

def main():
    gs.init()
    scene = gs.Scene(show_viewer=True)

    # Floor
    scene.add_entity(gs.morphs.Plane())

    # Obstacles: cylinders and boxes arranged in a ring
    num_cylinders = 8
    num_boxes = 6
    cylinder_radius = 3.0
    box_radius = 5.0

    for i in range(num_cylinders):
        angle = 2 * np.pi * i / num_cylinders
        x = cylinder_radius * np.cos(angle)
        y = cylinder_radius * np.sin(angle)
        scene.add_entity(
            gs.morphs.Cylinder(
                pos=(x, y, 0.5),
                radius=0.3,
                height=1.0,
            ),
            material=gs.materials.Rigid(),
        )

    for i in range(num_boxes):
        angle = 2 * np.pi * i / num_boxes + np.pi / num_boxes
        x = box_radius * np.cos(angle)
        y = box_radius * np.sin(angle)
        scene.add_entity(
            gs.morphs.Box(
                pos=(x, y, 0.5),
                size=(0.8, 0.8, 1.0),
            ),
            material=gs.materials.Rigid(),
        )

    # Mobile robot: a simple rigid box
    robot = scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 0.3),
            size=(0.6, 0.4, 0.3),
        ),
        material=gs.materials.Rigid(),
    )

    # LiDAR sensor
    lidar = scene.add_sensor(gs.sensors.Lidar())

    scene.build()

    # Simulation loop – robot moves forward and lidar scans
    try:
        while scene.viewer.is_running():
            pos = robot.get_position()
            if pos is not None:
                new_pos = np.array(pos) + np.array([0.02, 0.0, 0.0])
                robot.set_position(new_pos)
                lidar.set_position(new_pos)
            scene.step()
    except KeyboardInterrupt:
        pass
    finally:
        gs.exit()

if __name__ == "__main__":
    main()
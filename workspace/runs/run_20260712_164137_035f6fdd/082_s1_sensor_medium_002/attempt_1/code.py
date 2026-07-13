import numpy as np
import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(show_viewer=True)

    # Ground plane
    scene.add_entity(gs.morphs.Plane())

    # Obstacles: ring of cylinders
    num_cylinders = 8
    cylinder_radius = 0.3
    ring_radius = 3.0
    for i in range(num_cylinders):
        angle = i * 2 * np.pi / num_cylinders
        x = ring_radius * np.cos(angle)
        y = ring_radius * np.sin(angle)
        scene.add_entity(
            gs.morphs.Cylinder(
                pos=(x, y, 0.5),
                radius=cylinder_radius,
                height=1.0,
                fixed=True,
            ),
            material=gs.materials.Rigid(),
        )

    # Outer ring of boxes
    num_boxes = 6
    box_ring_radius = 5.0
    for i in range(num_boxes):
        angle = i * 2 * np.pi / num_boxes
        x = box_ring_radius * np.cos(angle)
        y = box_ring_radius * np.sin(angle)
        scene.add_entity(
            gs.morphs.Box(
                pos=(x, y, 0.5),
                size=(0.5, 0.5, 0.5),
                fixed=True,
            ),
            material=gs.materials.Rigid(),
        )

    # Mobile robot: a simple box chassis
    robot = scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 0.15),  # half the height to sit on the ground
            size=(0.8, 0.6, 0.3),
        ),
        material=gs.materials.Rigid(),
    )

    # Attach LiDAR to robot's base link
    robot_link = robot.links[0]  # base link of the box
    lidar_sensor = scene.add_sensor(
        gs.sensors.Lidar(n_rays=720, max_range=10.0, fov=360),
        link=robot_link,
    )

    scene.build()

    # Simulation with robot moving forward
    for _ in range(1000):
        # Move robot forward along global x-axis at 0.5 m/s
        robot.set_dofs_velocity([0.5, 0, 0, 0, 0, 0])
        scene.step()

if __name__ == "__main__":
    main()
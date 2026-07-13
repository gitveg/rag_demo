import numpy as np
import genesis as gs

# Initialize Genesis
gs.init(backend=gs.gpu)

# Scene setup with viewer
scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(6.0, 6.0, 5.0),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=40,
    ),
    show_viewer=True,
)

# Ground plane
plane = scene.add_entity(gs.morphs.Plane())

# Obstacles: cylinders and boxes in a ring
num_cylinders = 8
num_boxes = 6
cylinder_ring_radius = 3.0
box_ring_radius = 5.0

for i in range(num_cylinders):
    angle = i * 2 * np.pi / num_cylinders
    x = cylinder_ring_radius * np.cos(angle)
    y = cylinder_ring_radius * np.sin(angle)
    scene.add_entity(
        gs.morphs.Cylinder(
            radius=0.15,
            height=0.6,
            pos=(x, y, 0.3),
        )
    )

for i in range(num_boxes):
    angle = i * 2 * np.pi / num_boxes
    x = box_ring_radius * np.cos(angle)
    y = box_ring_radius * np.sin(angle)
    scene.add_entity(
        gs.morphs.Box(
            size=(0.4, 0.4, 0.4),
            pos=(x, y, 0.2),
        )
    )

# Simple mobile robot: a box base and a cylinder top
robot_base = scene.add_entity(
    gs.morphs.Box(
        size=(0.5, 0.3, 0.1),
        pos=(0.0, 0.0, 0.05),
    )
)
robot_top = scene.add_entity(
    gs.morphs.Cylinder(
        radius=0.12,
        height=0.3,
        pos=(0.0, 0.0, 0.25),
    )
)

# Lidar sensor attached to the robot (moved manually each step)
lidar = scene.add_sensor(
    gs.options.sensors.Lidar(
        pattern=gs.options.sensors.SphericalPattern()
    )
)

scene.build()

# Simulation loop: move robot forward and reposition lidar
for step in range(1000):
    # Move robot along the x-axis
    x = 0.01 * step
    robot_base.set_pos(np.array([x, 0.0, 0.05]))
    robot_top.set_pos(np.array([x, 0.0, 0.25]))

    # Update lidar pose to follow the robot
    lidar.set_pose(
        pos=np.array([x, 0.0, 0.35]),
        lookat=np.array([x + 1.0, 0.0, 0.35]),
    )

    scene.step()
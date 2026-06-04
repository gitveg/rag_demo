import genesis as gs
import numpy as np

gs.init()

scene = gs.Scene()

# Ground plane
scene.add_entity(morph=gs.morphs.Plane())

# Rotating rigid box on the ground
box = scene.add_entity(
    morph=gs.morphs.Box(size=(0.5, 0.5, 0.5), pos=(1.0, 0.0, 0.25)),
)

# Fixed pole (cylinder) on the ground
pole = scene.add_entity(
    morph=gs.morphs.Cylinder(height=2.0, radius=0.1, pos=(0.0, 0.0, 1.0)),
)

# LiDAR sensor mounted on top of the pole, pointing towards the box
lidar = scene.add_sensor(
    gs.options.sensors.Lidar(
        pose=(
            (0.0, 0.0, 2.0),          # position at top of pole
            (1.0, 0.0, 0.0, 0.0),     # quaternion pointing along +x (towards box)
        ),
    )
)

scene.build()

# Set the box rotating around its vertical axis (z)
box.set_dofs_velocity(np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0]))

point_clouds = []

for i in range(500):
    scene.step()
    # Read LiDAR point cloud
    data = lidar.get_data()
    points = data['points']  # (N, 3) array
    point_clouds.append(points)

print(f"Captured {len(point_clouds)} point clouds, each with {points.shape[0]} points.")
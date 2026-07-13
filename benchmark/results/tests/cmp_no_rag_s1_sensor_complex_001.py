import genesis as gs

gs.init()

scene = gs.Scene(show_viewer=False)

plane = scene.add_entity(
    gs.morphs.Plane(),
)

box = scene.add_entity(
    gs.morphs.Box(pos=(0, 0, 1.0), size=(0.5, 0.5, 0.5)),
    material=gs.materials.Rigid(),
)

# set box spinning
box.set_velocity(ang=(0, 0, 5.0))

# mount a lidar on a pole pointing at the box
lidar = scene.add_lidar(
    pos=(2.0, 0.0, 1.0),
    lookat=(0, 0, 1.0),
)

scene.build()

# capture point clouds over a few frames
points_over_time = []
for i in range(100):
    scene.step()
    points = lidar.get_point_cloud()
    points_over_time.append(points)
    print(f"Step {i}: {points.shape} points")

# Optionally save or process the collected data
# (here we just confirm collection)
print("Simulation finished. Total frames with point cloud:", len(points_over_time))
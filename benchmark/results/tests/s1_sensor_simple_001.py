"""
User Query: Attach a depth camera to a static sphere and render the depth map of the scene.
task_id: s1_sensor_simple_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    renderer=gs.options.renderers.Rasterizer(),
)

ground = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(friction=0.8),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

sphere = scene.add_entity(
    gs.morphs.Sphere(pos=(0.0, 0.0, 0.5), radius=0.2, fixed=True),
    material=gs.materials.Rigid(friction=0.5),
    surface=gs.surfaces.Glass(color=(0.3, 0.6, 0.9, 0.5)),
)

box = scene.add_entity(
    gs.morphs.Box(pos=(1.0, 0.0, 0.3), size=(0.4, 0.4, 0.6)),
    material=gs.materials.Rigid(friction=0.6),
    surface=gs.surfaces.Default(color=(0.9, 0.3, 0.3, 1.0)),
)

pattern = gs.sensors.DepthCameraPattern(
    res=(640, 480),
    fov_horizontal=60.0,
)

depth_opts = gs.sensors.DepthCamera(
    pattern=pattern,
    entity_idx=sphere.idx,
    link_idx_local=0,
    pos_offset=(0.0, 0.0, 0.25),
)

depth_cam = scene.add_sensor(depth_opts)

scene.build()

for _ in range(10):
    scene.step()

data = depth_cam.read()
depth_img = depth_cam.read_image()

print("Point cloud shape:", tuple(data.points.shape))
print("Distances shape:", tuple(data.distances.shape))
print("Depth image shape:", tuple(depth_img.shape))
print("Depth image dtype:", depth_img.dtype)
print("Depth min:", float(depth_img.min()))
print("Depth max:", float(depth_img.max()))
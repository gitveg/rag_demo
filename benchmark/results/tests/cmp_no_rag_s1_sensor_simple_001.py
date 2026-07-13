import genesis as gs

gs.init()
scene = gs.Scene()

# ground plane
plane = scene.add_entity(gs.morphs.Plane())

# static sphere at center
sphere = scene.add_entity(
    gs.morphs.Sphere(pos=(0.0, 0.0, 0.5), radius=0.1),
    fixed=True,
)

# create depth camera and attach it to the sphere
cam = scene.add_camera(
    res=(640, 480),
    pos=(0.5, 0.5, 1.0),
    lookat=(0.0, 0.0, 0.5),
)
cam.attach(sphere)

# set local offset so the camera stays near the sphere
cam.set_pose(
    pos=(0.15, 0.15, 0.2),
    lookat=(0.0, 0.0, 0.0),
)

scene.build()

# render depth map
result = cam.render(rgb=False, depth=True)
depth_img = result["depth"]
print("Depth image shape:", depth_img.shape)
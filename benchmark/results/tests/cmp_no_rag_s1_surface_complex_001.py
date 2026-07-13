import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.5, -2.5, 1.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=40,
    ),
)

# Ground plane
plane = scene.add_entity(gs.morphs.Plane())

# Load robot arm with polished metallic look
robot = scene.add_entity(
    gs.morphs.MJCF(
        file="robot_arm.xml",
    ),
    material=gs.materials.Rigid(
        color=(0.8, 0.8, 0.8),
        metallic=1.0,
        roughness=0.05,
    ),
)

# Translucent red box in front of the robot
box = scene.add_entity(
    gs.morphs.Box(
        pos=(0.6, 0.0, 0.02),
        size=(0.4, 0.4, 0.02),
    ),
    material=gs.materials.Rigid(
        color=(1.0, 0.0, 0.0, 0.6),
        roughness=0.5,
    ),
)

scene.build()
import genesis as gs

gs.init()

# Create scene
scene = gs.Scene()

# Ground
scene.add_entity(gs.morphs.Plane())

# Platform (box)
platform = scene.add_entity(
    gs.morphs.Box(pos=(0.5, 0.0, 0.1), size=(0.4, 0.4, 0.2)),
    surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5))
)

# Small cube to pick
cube = scene.add_entity(
    gs.morphs.Box(pos=(0.3, -0.2, 0.1), size=(0.05, 0.05, 0.05)),
    surface=gs.surfaces.Default(color=(1.0, 0.0, 0.0))
)

# Robotic arm (UR5)
robot = scene.add_entity(
    gs.morphs.URDF(
        file="ur5/ur5.urdf",
        pos=(0.3, 0.2, 0.0),
        fixed=True
    ),
)

scene.build()

# Control: move to pick
pick_joint_angles = [0.0, -1.5, 1.5, 0.0, 1.5, 0.0]
place_joint_angles = [0.5, -1.2, 1.2, 0.0, 1.2, 0.0]

# Simulation loop - move to pick location
for _ in range(500):
    robot.set_dof_position_target(pick_joint_angles)
    scene.step()

# Grasp: attach cube to end effector
ee_link = robot.get_link("ee_link")
cube.set_attached(ee_link)

# Move to place location
for _ in range(500):
    robot.set_dof_position_target(place_joint_angles)
    scene.step()

# Release cube
cube.set_attached(None)

# Let cube settle
for _ in range(200):
    scene.step()
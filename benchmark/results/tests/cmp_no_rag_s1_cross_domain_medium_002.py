import genesis as gs

# Initialize Genesis
gs.init(backend='cpu')

# Create scene with gravity and viewer
scene = gs.Scene(gravity=(0, 0, -9.81), show_viewer=True)

# Add a rigid table (box)
table = scene.add_entity(
    gs.morphs.Box(pos=(0.5, 0, -0.05), size=(1.0, 1.0, 0.1)),
    surface=gs.surfaces.Rigid()
)

# Add a rigid sphere on the table
sphere = scene.add_entity(
    gs.morphs.Sphere(pos=(0.7, 0.2, 0.05), radius=0.05),
    surface=gs.surfaces.Rigid()
)

# Add a piece of cloth (plane shape as cloth) lying flat near the sphere
cloth = scene.add_entity(
    gs.morphs.Plane(pos=(0.3, 0.0, 0.005), euler=(0, 0, 0), halfsize=(0.2, 0.2)),
    surface=gs.surfaces.SoftDeformable(),
    material=gs.materials.FEM()
)

# Add a UR5 robotic arm with a suction gripper
robot = scene.add_entity(
    gs.robots.UR5(
        pos=(0.0, 0.0, 0.0),
        eef_type='suction'
    )
)

# Build the scene
scene.build()

# Simulation loop: pick up cloth, move over sphere, drop, and wait
# Define key waypoints in joint space (6 joints + 2 finger joints)
q_home = robot.q0.copy()            # initial default pose
q_over_cloth = robot.inverse_kinematics(gs.math.Vec3(0.3, 0.0, 0.05))  # where cloth lies
q_over_sphere = robot.inverse_kinematics(gs.math.Vec3(0.7, 0.2, 0.15))  # above sphere

# Move to cloth pick position
for _ in range(200):
    robot.control_dofs_position(q_over_cloth, stiffness=0.5, damping=0.1)
    scene.step()

# Suction grip
robot.grasp()

# Lift cloth
q_lift = q_over_cloth.copy()
q_lift[2] += 0.2  # lift end-effector a bit (imprecise but simple)
for _ in range(100):
    robot.control_dofs_position(q_lift, stiffness=0.5, damping=0.1)
    scene.step()

# Move to above sphere
for _ in range(300):
    robot.control_dofs_position(q_over_sphere, stiffness=0.5, damping=0.1)
    scene.step()

# Release cloth
robot.release()

# Wait for cloth to settle on sphere
for _ in range(1000):
    scene.step()

# Keep simulation running until user closes viewer
while True:
    scene.step()
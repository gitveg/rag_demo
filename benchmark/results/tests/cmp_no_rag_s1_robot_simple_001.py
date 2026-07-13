import genesis as gs

gs.init()
scene = gs.Scene()

# Load the Franka Panda robot from the MJCF file
robot = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
scene.build()

# Get current joint positions (list of all dofs)
current_pos = robot.get_dofs_position()

# Set the first joint to 45 degrees (convert to radians)
target_angle = 45.0 * 3.1415926535 / 180.0
current_pos[0] = target_angle

# Apply the updated positions
robot.set_dofs_position(current_pos)

# Step the simulation once to commit the state
scene.step()
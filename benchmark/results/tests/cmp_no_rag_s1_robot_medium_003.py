import genesis as gs

gs.init()

scene = gs.Scene()

robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

# Target end‑effector position
target_pos = (0.3, 0.2, 0.4)

# End‑effector link (standard name in the Franka Panda MJCF)
ee_link = robot.get_link("panda_hand")

# Solve inverse kinematics
qpos = robot.inverse_kinematics(link=ee_link, pos=target_pos)

# Apply joint command
robot.set_dofs_position(qpos)

# Run a few simulation steps to propagate the command
for _ in range(10):
    scene.step()

# Verify the achieved position
achieved_pos = ee_link.get_pos()
print(f"End‑effector position: {achieved_pos}")
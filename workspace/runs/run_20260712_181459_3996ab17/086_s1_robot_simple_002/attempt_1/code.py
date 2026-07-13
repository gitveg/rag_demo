import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene()

# Add a ground plane and the Franka Panda robot
plane = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))

scene.build()

# Target joint angles (roughly places end effector above the table)
target_qpos = [0.0, -0.5, 0.0, -2.0, 0.0, 1.5, 0.5]

# Simulate moving to the target position
for _ in range(500):
    franka.set_qpos(target_qpos)  # sets the robot's joint positions to the target
    scene.step()
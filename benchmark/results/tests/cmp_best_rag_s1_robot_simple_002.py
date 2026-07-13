import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(show_viewer=True)

plane = scene.add_entity(gs.morphs.Plane())
# Add a table as a fixed box above the plane
table = scene.add_entity(
    gs.morphs.Box(
        pos=(0.5, 0.0, 0.2),   # center of the table
        size=(0.3, 0.3, 0.1),  # width, depth, height
        fixed=True,
    )
)

franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

scene.build()

# Set PD gains (position and velocity) for all joints
dof_kp = [100.0] * franka.n_dofs
dof_kv = [20.0] * franka.n_dofs
franka.set_dofs_kp(dof_kp)
franka.set_dofs_kv(dof_kv)

# Target joint configuration that places the end-effector above the table
# (example raised pose: shoulder up, elbow bent, wrist pointing down)
target_q = [0.0, -0.5, 0.0, -2.0, 0.0, 1.5, 0.0, 0.04, 0.04]

# Control loop: step simulation while commanding the target joint positions
for _ in range(500):
    franka.control_dofs_position(target_q)
    scene.step()
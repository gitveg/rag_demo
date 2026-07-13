import genesis as gs

########################## init ##########################
gs.init()

########################## create a scene ##########################
dt = 1e-3
scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        substeps=10,
        gravity=(0, 0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(1.5, 0, 0.8),
        camera_lookat=(0.0, 0.0, 0.3),
        camera_fov=40,
    ),
    mpm_options=gs.options.MPMOptions(
        dt=dt,
        lower_bound=(-1.0, -1.0, -0.2),
        upper_bound=(1.0, 1.0, 1.0),
    ),
    vis_options=gs.options.VisOptions(show_world_frame=False),
    show_viewer=True,
)

########################## entities ##########################
# ground plane
scene.add_entity(morph=gs.morphs.Plane())

# soft MPM elastic sphere – placed between fingers later
sphere = scene.add_entity(
    material=gs.materials.MPM.Elastic(E=1e4, rho=400),
    morph=gs.morphs.Sphere(
        pos=(0.4, 0.0, 0.28),
        radius=0.04,
    ),
    surface=gs.surfaces.Default(
        color=(0.4, 1.0, 0.4),
        vis_mode="particle",
    ),
)

# articulated robotic gripper (Panda arm with gripper)
robot = scene.add_entity(
    morph=gs.morphs.MJCF(
        file="xml/franka_emika_panda/scene.xml",
        pos=(0.0, 0.0, 0.0),
        euler=(0.0, 0.0, 0.0),
    ),
)

########################## build and configure ##########################
scene.build()

# set a joint configuration that brings the gripper horizontally to the sphere
joint_target = [0.0, -0.4, 0.0, -2.2, 0.0, 1.5, 0.0, 0.02, 0.02]  # 7 arm + 2 gripper
robot.set_dofs_position(joint_target)

########################## simulation loop ##########################
scene.start_recording()
for _ in range(1000):
    scene.step()

scene.viewer.save_video("gripper_soft_sphere.mp4")
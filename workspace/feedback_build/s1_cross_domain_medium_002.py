import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(gs.morphs.Plane())

franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

sphere = scene.add_entity(
    gs.morphs.Sphere(
        pos=(0.5, 0.5, 0.2),
        radius=0.2,
    ),
    material=gs.materials.Rigid(),
)

cloth = scene.add_entity(
    material=gs.materials.PBD.Cloth(),
    morph=gs.morphs.Mesh(
        file="meshes/cloth.obj",
        scale=1.0,
        pos=(0.5, 0.5, 0.02),
        euler=(0.0, 0.0, 0.0),
    ),
    surface=gs.surfaces.Default(
        color=(0.2, 0.4, 0.8, 1.0),
    ),
)

scene.build()

# Simple script to move the arm, grasp, lift, move over sphere, and release
for i in range(1000):
    if i < 200:
        # Home, fingers open
        franka.set_qpos([0.0, 0.0, 0.0, -1.57, 0.0, 1.57, 0.78, 0.04, 0.04])
    elif i < 400:
        # Move end-effector above cloth (approx)
        franka.set_qpos([0.0, -0.8, 0.0, -2.4, 0.0, 2.0, 0.8, 0.04, 0.04])
    elif i < 600:
        # Close gripper to grasp cloth
        franka.set_qpos([0.0, -0.8, 0.0, -2.4, 0.0, 2.0, 0.8, 0.0, 0.0])
    elif i < 800:
        # Lift
        franka.set_qpos([0.0, -0.2, 0.0, -1.0, 0.0, 1.0, 1.0, 0.0, 0.0])
    else:
        # Move over sphere and open fingers to release cloth
        franka.set_qpos([0.0, 0.1, 0.0, -1.2, 0.0, 1.2, 0.9, 0.04, 0.04])
    scene.step()
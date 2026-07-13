import genesis as gs

gs.init(backend=gs.gpu)

scene = gs.Scene(
    show_viewer=True,
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.5, 0.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
    ),
)

plane = scene.add_entity(gs.morphs.Plane())

gripper = scene.add_entity(
    gs.morphs.URDF(
        file='robotiq_2f85.urdf',
        pos=(0.0, 0.0, 0.5),
        fixed=True,
    )
)

sphere = scene.add_entity(
    gs.morphs.Sphere(
        pos=(0.0, 0.0, 0.7),
        radius=0.04,
    ),
    material=gs.materials.MPM.Elastic(
        E=1e5,
        nu=0.3,
        density=1000,
    ),
    surface=gs.surfaces.Default(visualization=True)
)

scene.build()

for _ in range(1000):
    scene.step()
    scene.render()
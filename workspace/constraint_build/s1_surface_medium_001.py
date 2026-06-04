import genesis as gs

gs.init(backend=gs.gpu)

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.5, 0.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.0),
    ),
    show_viewer=True,
)

sphere = scene.add_entity(
    morph=gs.options.morphs.Sphere(
        pos=(1.0, 0.5, 0.0),
        radius=0.5,
    ),
    material=gs.materials.Rigid(),
)

box = scene.add_entity(
    morph=gs.options.morphs.Mesh(
        file='cube.obj',
        pos=(-1.0, 0.5, 0.0),
        scale=0.5,
    ),
    material=gs.materials.Rigid(),
)

scene.build()

for i in range(1000):
    scene.step()
import genesis as gs

gs.init(backend='gpu')

scene = gs.Scene(
    show_viewer=True,
    viewer_options=gs.options.ViewerOptions(
        res=(1280, 720),
        camera_pos=(3, 2, 2),
        camera_lookat=(0, 0, 0.5),
    ),
)

plane = scene.add_entity(gs.morphs.Plane())
fluid = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 1.0), size=(0.2, 0.2, 0.2)),
    material=gs.materials.Fluid(),
)

scene.build()

while True:
    scene.step()
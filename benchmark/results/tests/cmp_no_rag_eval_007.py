import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(5, 2, 5),
        camera_lookat=(0, 0, 1),
    ),
)

plane = scene.add_entity(gs.morphs.Plane())

box_size = (1.0, 1.0, 1.0)
box1 = scene.add_entity(
    gs.morphs.Box(pos=(0, 0, 0.5), size=box_size),
)
box2 = scene.add_entity(
    gs.morphs.Box(pos=(0, 0, 1.5), size=box_size),
)
box3 = scene.add_entity(
    gs.morphs.Box(pos=(0, 0, 2.5), size=box_size),
)

scene.build()

for _ in range(500):
    scene.step()
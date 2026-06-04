import genesis as gs

gs.init()

scene = gs.Scene(show_viewer=False)

scene.add_entity(morph=gs.morphs.Plane())

cube1 = scene.add_entity(
    morph=gs.morphs.Box(
        size=(0.3, 0.3, 0.3),
        pos=(0.3, 0.3, 0.1),
        vel=(0.5, 0.0, 0.0),
    )
)

cube2 = scene.add_entity(
    morph=gs.morphs.Box(
        size=(0.3, 0.3, 0.3),
        pos=(0.7, 0.7, 0.1),
        vel=(-0.5, 0.0, 0.0),
    )
)

scene.build()

camera_above = scene.add_camera(
    pos=(0.5, 2.5, 3.5),
    lookat=(0.5, 0.5, 0.5),
)

camera_ground = scene.add_camera(
    pos=(0.5, 1.0, 0.5),
    lookat=(0.5, 0.5, 0.5),
)

for i in range(200):
    scene.step()
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        substeps=10,
        gravity=(0, 0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(0, -3.5, 2.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=40,
    ),
    show_viewer=True,
)

plane = scene.add_entity(gs.morphs.Plane())
bunny = scene.add_entity(
    gs.morphs.Mesh(file='meshes/bunny.obj', pos=(0, 0, 2)),
    material=gs.materials.PBD.Elastic(),
)

scene.build()

for _ in range(500):
    scene.step()
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
        substeps=5,
    ),
    fem_options=gs.options.FEMOptions(),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(0, -2, 1.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=40,
    ),
    show_viewer=True,
)

plane = scene.add_entity(gs.morphs.Plane())

cube_soft = scene.add_entity(
    material=gs.materials.FEM.Elastic(E=1e5),
    morph=gs.morphs.Box(pos=(0.15, 0.0, 0.5), size=(0.1, 0.1, 0.1)),
)

cube_stiff = scene.add_entity(
    material=gs.materials.FEM.Elastic(E=1e6),
    morph=gs.morphs.Box(pos=(-0.15, 0.0, 0.5), size=(0.1, 0.1, 0.1)),
)

scene.build()

for _ in range(500):
    scene.step()
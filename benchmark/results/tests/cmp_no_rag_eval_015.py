import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        gravity=(0, 0, -9.81),
        dt=0.01,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3, 3, 3),
        camera_lookat=(0, 0, 1),
        res=(800, 600),
    ),
)

# static ground
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(fixed=True),
)

# block of liquid water
liquid = scene.add_entity(
    material=gs.materials.Fluid(),
    morph=gs.morphs.Box(pos=(0.0, 0.0, 2.0), size=(0.5, 0.5, 0.5)),
    surface=gs.surfaces.Default(color=(0.3, 0.5, 1.0)),
)

scene.build()

for i in range(1000):
    scene.step()
    scene.render()
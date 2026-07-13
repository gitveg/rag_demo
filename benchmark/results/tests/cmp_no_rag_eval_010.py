import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
        gravity=(0.0, 0.0, 0.0),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, 3.0, 3.0),
        camera_lookat=(0.0, 0.0, 0.0),
    ),
)

sphere1 = scene.add_entity(
    gs.morphs.Sphere(radius=0.3, pos=(1.5, 0.0, 0.0)),
    material=gs.materials.Rigid(),
)

sphere2 = scene.add_entity(
    gs.morphs.Sphere(radius=0.3, pos=(-1.5, 0.0, 0.0)),
    material=gs.materials.Rigid(),
)

scene.build()

sphere1.set_dofs_velocity([-0.5, 0.0, 0.0, 0.0, 0.0, 0.0])
sphere2.set_dofs_velocity([0.5, 0.0, 0.0, 0.0, 0.0, 0.0])

for _ in range(600):
    scene.step()
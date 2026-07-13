import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
        gravity=(0, 0, 0),
    ),
)

camera = scene.add_camera(
    res=(640, 480),
    pos=(3, 3, 3),
    lookat=(0, 0, 0),
    fov=30,
)

scene.add_light(
    pos=(3, 3, 3),
    lookat=(0, 0, 0),
    intensity=1000,
)

sphere = scene.add_entity(
    gs.morphs.Sphere(
        pos=(0.0, 0.0, 0.0),
        radius=1.0,
    ),
    material=gs.materials.Rigid(),
)

scene.build()

scene.viewer.set_camera(camera)

for _ in range(2000):
    scene.step()

scene.viewer.start()
while scene.viewer.is_alive():
    scene.step()
    scene.viewer.render()
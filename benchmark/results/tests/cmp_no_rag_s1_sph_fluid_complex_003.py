import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.001,
        gravity=(0.0, 0.0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, -3.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.3),
    ),
)

bowl = scene.add_entity(
    gs.morphs.Mesh(
        file="meshes/bowl.obj",
        pos=(0.0, 0.0, 0.0),
        fixed=True,
    ),
    material=gs.materials.Rigid(),
)

emitter = scene.add_entity(
    gs.morphs.Sphere(
        radius=0.03,
        pos=(0.4, -0.4, 0.7),
    ),
    material=gs.materials.Fluid(),
    is_emitter=True,
    emitter_velocity=(2.0, -2.0, -1.5),
    emitter_rate=500,
)

scene.build()

for _ in range(2000):
    scene.step()
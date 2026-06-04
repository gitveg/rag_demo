import genesis as gs

gs.init(backend=gs.gpu)

scene = gs.Scene(
    show_viewer=True,
    vis_options=gs.options.VisOptions(
        plane_reflection=False,
    ),
    rigid_options=gs.options.RigidOptions(
        dt=0.01,
    ),
)

plane = scene.add_entity(morph=gs.options.morphs.Plane())
ball = scene.add_entity(
    morph=gs.options.morphs.Sphere(pos=(0.0, 0.0, 1.0), radius=0.1),
    material=gs.materials.Rigid(coup_restitution=0.9),
)

scene.build()

camera = scene.add_camera(
    pos=(2.0, 2.0, 3.0),
    lookat=(0.0, 0.0, 0.0),
    up=(0.0, 0.0, 1.0),
    fov=30,
)

scene.start_recording()

for _ in range(500):
    scene.step()

scene.stop_recording()
scene.viewer.save_video("bouncing_ball.mp4")
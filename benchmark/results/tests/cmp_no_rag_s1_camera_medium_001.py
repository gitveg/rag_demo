import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
        gravity=(0, 0, -9.81),
    ),
)

plane = scene.add_entity(
    gs.morphs.Plane(),
)
sphere = scene.add_entity(
    gs.morphs.Sphere(
        pos=(0, 0, 2.0),
        radius=0.5,
    ),
    material=gs.materials.Rigid(),
    surface=gs.surfaces.Diffuse(color=(1.0, 0.0, 0.0)),
)

scene.build()

camera = scene.add_camera(
    pos=(0, 5, 5),   # 45° elevation from horizontal
    lookat=(0, 0, 0.5),
    fov=45,
)

renderer = scene.add_renderer(
    gs.renderers.CameraRenderer(
        camera=camera,
        resolution=(640, 480),
    )
)
recording = scene.add_recording(
    gs.recordings.VideoRecorder(
        renderer=renderer,
        dirname="output",
        filename="red_sphere_falling.mp4",
    )
)

for _ in range(300):
    scene.step()

scene.stop_recording()
gs.tools.clean()
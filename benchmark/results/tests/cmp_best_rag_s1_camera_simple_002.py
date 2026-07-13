import genesis as gs

gs.init()

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        res=(1280, 960),
        camera_pos=(0.0, 4.0, 1.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=40,
        max_FPS=60,
    ),
    vis_options=gs.options.VisOptions(
        show_world_frame=True,
        world_frame_size=1.0,
    ),
    renderer=gs.renderers.Rasterizer(),
    show_viewer=True,
)

plane = scene.add_entity(
    morph=gs.options.morphs.Plane(),
)

ball = scene.add_entity(
    morph=gs.options.morphs.Sphere(
        pos=(0.0, 0.0, 2.0),
        radius=0.2,
    ),
    material=gs.materials.Rigid(),
)

scene.build()

scene.start_recording()

for i in range(300):
    scene.step()

scene.stop_recording()
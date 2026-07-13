import genesis as gs

def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(enable_collision=False, gravity=(0, 0, 0)),
        viewer_options=gs.options.ViewerOptions(
            res=(1920, 1080),
            camera_pos=(5, -5, 3),
            camera_lookat=(0, 0, 0.5),
            camera_fov=50,
        ),
        renderer=gs.renderers.RayTracer(),
        show_viewer=True,
    )

    # Polished floor
    floor = scene.add_entity(
        morph=gs.morphs.Plane(pos=(0, 0, 0), normal=(0, 0, 1)),
        surface=gs.options.surfaces.Smooth(),
    )

    # Sports car body with glossy paint
    car_body = scene.add_entity(
        morph=gs.morphs.Mesh(file='car_body.obj', pos=(0, 0, 0.5)),
        surface=gs.options.surfaces.Smooth(color=(0.9, 0.1, 0.1, 1.0)),
    )

    # Reflective windows
    car_windows = scene.add_entity(
        morph=gs.morphs.Mesh(file='car_windows.obj', pos=(0, 0, 0.5)),
        surface=gs.options.surfaces.Glass(),
    )

    # Metallic wheels
    wheel_positions = [(0.8, 1.0, 0.3), (-0.8, 1.0, 0.3), (0.8, -1.0, 0.3), (-0.8, -1.0, 0.3)]
    for pos in wheel_positions:
        scene.add_entity(
            morph=gs.morphs.Mesh(file='wheel.obj', pos=pos),
            surface=gs.options.surfaces.Aluminium(),
        )

    scene.build()

    # Keep the viewer open
    try:
        while True:
            scene.step()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
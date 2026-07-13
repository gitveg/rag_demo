import genesis as gs


def main():
    # Initialize Genesis
    gs.init(precision="32", logging_level="info")

    # Create the showroom scene with ray tracing for reflections
    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(enable_collision=False, gravity=(0, 0, 0)),
        viewer_options=gs.options.ViewerOptions(
            res=(1920, 1080),
            camera_pos=(5.0, -3.0, 2.5),
            camera_lookat=(3.0, 0.0, 0.5),
            camera_fov=50,
        ),
        renderer=gs.renderers.RayTracer(),
        show_viewer=True,
    )

    # Polished reflective floor
    floor = scene.add_entity(
        morph=gs.morphs.Plane(),
        surface=gs.options.surfaces.Smooth(color=(0.6, 0.6, 0.6, 1.0)),
    )

    # Car body – glossy red paint
    car_body = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(3.0, 0.0, 0.5),
            size=(2.0, 0.8, 0.5),
        ),
        surface=gs.options.surfaces.Smooth(color=(0.9, 0.1, 0.1, 1.0)),
    )

    # Windshield – reflective glass
    windshield = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(3.0, 0.0, 1.05),
            size=(1.0, 0.7, 0.6),
        ),
        surface=gs.options.surfaces.Glass(),
    )

    # Metallic wheels (using spheres to approximate wheels)
    wheel_centers = [
        (2.2, -0.5, 0.25),
        (2.2, 0.5, 0.25),
        (3.8, -0.5, 0.25),
        (3.8, 0.5, 0.25),
    ]
    for pos in wheel_centers:
        scene.add_entity(
            morph=gs.morphs.Sphere(pos=pos, radius=0.3),
            surface=gs.options.surfaces.Aluminium(),
        )

    # Build the scene
    scene.build()

    # Keep the viewer open
    try:
        while True:
            scene.step()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
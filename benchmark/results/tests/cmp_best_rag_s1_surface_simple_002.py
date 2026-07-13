import genesis as gs


def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        renderer=gs.renderers.RayTracer(),
        viewer_options=gs.options.ViewerOptions(
            res=(1920, 1080),
            camera_pos=(3.0, -3.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=True,
    )

    # Ground plane
    scene.add_entity(
        gs.options.morphs.Plane(),
        surface=gs.options.surfaces.Rough(),
    )

    # Shiny metallic sphere with reflective silver appearance
    scene.add_entity(
        gs.options.morphs.Sphere(pos=(0.0, 0.0, 0.5), radius=0.5),
        surface=gs.options.surfaces.Aluminium(),
    )

    scene.build()

    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
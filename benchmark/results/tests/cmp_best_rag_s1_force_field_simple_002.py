import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 3.0, 2.5),
            camera_lookat=(0.0, 0.0, 2.0),
        ),
        show_viewer=True,
    )

    # Ground plane for reference
    scene.add_entity(
        morph=gs.options.morphs.Plane(),
        material=gs.materials.Rigid(),
    )

    # Lightweight sphere suspended in the air
    scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(0.0, 0.0, 3.0),
            radius=0.3,
        ),
        material=gs.materials.Rigid(rho=10.0),
    )

    # Constant sideways wind
    scene.add_force_field(
        gs.force_fields.Wind(
            direction=(1, 0, 0),
            strength=5.0,
            radius=10,
            center=(0, 0, 3),
        )
    )

    scene.build()

    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
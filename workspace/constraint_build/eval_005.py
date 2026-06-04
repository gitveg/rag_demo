import genesis as gs


def main():
    gs.init()

    # Create a scene with zero gravity
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(gravity=(0.0, 0.0, 0.0)),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 0.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=True,
    )

    # Add a rigid sphere
    sphere = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            radius=0.5,
            pos=(0.0, 0.0, 0.0),
        ),
        material=gs.materials.Rigid(),
    )

    # Build the scene
    scene.build()

    # Run simulation for 500 steps
    for i in range(500):
        scene.step()


if __name__ == "__main__":
    main()
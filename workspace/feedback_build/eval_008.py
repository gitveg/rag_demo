import genesis as gs

def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(),
        viewer_options=gs.options.ViewerOptions(
            res=(800, 600),
            camera_pos=(3, 3, 1),
            camera_lookat=(0, 0, 0.25),
        ),
    )

    # Large static box
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0, 0, 0),
            size=(1.0, 1.0, 0.2),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )

    # Small falling sphere
    scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0, 0, 0.5),
            radius=0.05,
        ),
        material=gs.materials.Rigid(),
    )

    scene.build()

    # Run simulation for a few seconds
    for _ in range(300):
        scene.step()

if __name__ == "__main__":
    main()
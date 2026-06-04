import genesis as gs

def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=True,
    )

    # Ground plane
    plane = gs.options.morphs.Plane()
    scene.add_entity(plane)

    # Red rigid sphere falling from above
    sphere = gs.options.morphs.Sphere(
        radius=0.08,
        pos=(0.0, 0.0, 1.0),
    )
    scene.add_entity(sphere, material=gs.materials.Rigid())

    scene.build()

    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()
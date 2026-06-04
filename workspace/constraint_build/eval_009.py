import genesis as gs

def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=True,
    )

    # Ground plane
    plane = scene.add_entity(
        morph=gs.options.morphs.Plane(),
    )

    # Red rigid box
    box = scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(0.0, 0.0, 2.0),
        ),
        material=gs.materials.Rigid(),
    )

    # Blue rigid cylinder
    cylinder = scene.add_entity(
        morph=gs.options.morphs.Cylinder(
            pos=(0.0, 0.0, 2.0),
        ),
        material=gs.materials.Rigid(),
    )

    scene.build()

    for i in range(500):
        scene.step()

if __name__ == "__main__":
    main()
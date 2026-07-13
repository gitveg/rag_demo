import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=True,
    )

    sphere = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.0, 0.0, 2.0),
            radius=0.5,
        ),
        surface=gs.surfaces.Default(
            color=(1.0, 0.0, 0.0),
        ),
    )

    scene.build()

    while scene.viewer.is_alive():
        scene.step()

if __name__ == "__main__":
    main()
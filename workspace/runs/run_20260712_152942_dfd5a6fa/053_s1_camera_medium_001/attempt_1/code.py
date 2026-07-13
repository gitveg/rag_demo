import genesis as gs


def main():
    ########################## init ##########################
    gs.init(backend=gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(4.0, 0.0, 4.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=False,
    )

    ########################## entities ##########################
    plane = scene.add_entity(gs.morphs.Plane())

    sphere = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.0, 0.0, 2.0),
            radius=0.5,
        ),
        surface=gs.surfaces.Default(color=(1.0, 0.0, 0.0)),
    )

    ########################## build ##########################
    scene.build()

    ########################## record and simulate ##########################
    scene.start_recording()

    for _ in range(500):
        scene.step()

    scene.viewer.save_video(filename="output.mp4")


if __name__ == "__main__":
    main()
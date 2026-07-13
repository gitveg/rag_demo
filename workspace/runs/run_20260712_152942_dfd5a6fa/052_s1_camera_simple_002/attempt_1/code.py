import genesis as gs


def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            res=(1024, 768),
            camera_pos=(5.0, 5.0, 2.0),
            camera_lookat=(0.0, 0.0, 1.0),
            camera_fov=45,
        ),
        show_viewer=True,
        show_FPS=False,
    )

    ground = scene.add_entity(gs.morphs.Plane())
    ball = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.0, 0.0, 2.0),
            radius=0.1,
        ),
        material=gs.materials.Rigid(),
    )

    scene.build()

    scene.start_recording()  # start capturing frames

    for _ in range(300):
        scene.step()

    scene.viewer.save_video("ball_fall.mp4")


if __name__ == "__main__":
    main()
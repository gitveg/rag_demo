import genesis as gs


def main():
    ########################## init ##########################
    gs.init()

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            res=(1280, 720),
            camera_pos=(3.0, 0.0, 3.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        renderer=gs.renderers.Rasterizer(),
        show_viewer=False,
    )

    ########################## add entities ##########################
    plane = scene.add_entity(gs.options.morphs.Plane())

    sphere = scene.add_entity(
        gs.options.morphs.Sphere(pos=(0.0, 0.0, 2.0), radius=0.3),
        surface=gs.options.surfaces.Rough(
            color=(0.8, 0.1, 0.1),
        ),
    )

    ########################## build and simulate ##########################
    scene.build()

    scene.start_recording()
    for _ in range(200):
        scene.step()
    scene.stop_recording()


if __name__ == "__main__":
    main()
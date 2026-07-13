import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # Large static sphere
    sphere = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.0, 0.0, 0.0),
            radius=1.0,
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )

    # Small falling box
    box = scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 2.0),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.5, 1, 0.5)),
    )

    ########################## build ##########################
    scene.build()

    ########################## simulate ##########################
    if args.vis:
        while scene.viewer.is_alive():
            scene.step()
    else:
        for _ in range(500):
            scene.step()

    scene.viewer.stop()


if __name__ == "__main__":
    main()
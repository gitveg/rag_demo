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
            camera_pos=(3.0, 2.0, 2.5),
            camera_lookat=(0.0, 0.0, 1.0),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # large static sphere
    sphere = scene.add_entity(
        gs.morphs.Sphere(
            radius=1.0,
            pos=(0.0, 0.0, 1.0),
            fixed=True,
        ),
        surface=gs.surfaces.Default(color=(0.7, 0.7, 0.9)),
    )

    # small rigid box
    box = scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 2.5),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.5, 1.0, 0.5)),
    )

    ########################## build ##########################
    scene.build()

    ########################## simulate ##########################
    for _ in range(1000):
        scene.step()

    if args.vis:
        scene.viewer.stop()


if __name__ == "__main__":
    main()
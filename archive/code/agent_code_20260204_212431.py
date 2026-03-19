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
            camera_pos=(2.0, 0.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    ground = scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, -0.1),
            size=(10.0, 10.0, 0.2),
            fixed=True,
        ),
    )
    sphere = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.0, 0.0, 2.0),
            radius=0.2,
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build and run ##########################
    scene.build()
    for _ in range(300):
        scene.step()


if __name__ == "__main__":
    main()
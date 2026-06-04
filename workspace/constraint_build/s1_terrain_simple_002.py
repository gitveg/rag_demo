import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    scene = gs.Scene(
        show_viewer=args.vis,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, 2.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
    )

    # Sloped terrain
    plane = scene.add_entity(
        morph=gs.morphs.Plane(
            euler=(0.15, 0.0, 0.0),  # gentle slope around x axis
        ),
        material=gs.materials.Rigid(),
    )

    # Rigid sphere placed uphill
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            radius=0.1,
            pos=(0.0, 0.0, 0.5),
        ),
        material=gs.materials.Rigid(),
    )

    scene.build()

    for i in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
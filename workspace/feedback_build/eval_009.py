import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    # fixed ground plane so objects land
    scene.add_entity(
        gs.morphs.Box(pos=(0.0, 0.0, -0.01), size=(5.0, 5.0, 0.02), fixed=True),
    )

    # red box
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(pos=(0.0, 0.0, 1.0), size=(0.1, 0.1, 0.1)),
        surface=gs.surfaces.Default(color=(1, 0, 0)),
    )

    # blue cylinder
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Cylinder(pos=(0.2, 0.0, 1.0), radius=0.05, height=0.1),
        surface=gs.surfaces.Default(color=(0, 0, 1)),
    )

    scene.build()

    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
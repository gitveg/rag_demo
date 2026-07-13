import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    # Init
    gs.init(backend=gs.gpu if not args.vis else gs.cpu)

    # Scene
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, 2.0, 1.5),
            camera_lookat=(0.0, 0.0, 0.2),
            camera_fov=50,
        ),
        show_viewer=args.vis,
    )

    # Shallow basin (rigid)
    basin = scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.05),
            size=(0.6, 0.6, 0.1),
            fixed=True,
        ),
        surface=gs.surfaces.Default(color=(0.6, 0.8, 1.0, 1.0)),
    )

    # Water blob (liquid)
    water = scene.add_entity(
        material=gs.materials.SPH.Liquid(),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.3),
            size=(0.2, 0.2, 0.2),
        ),
        surface=gs.surfaces.Default(color=(0.2, 0.5, 1.0, 0.8)),
    )

    # Build scene
    scene.build()

    # Simulate
    for _ in range(200):
        scene.step()


if __name__ == "__main__":
    main()
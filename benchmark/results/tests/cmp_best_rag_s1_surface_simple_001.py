import argparse
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 3.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=args.vis,
    )

    # Ground plane (static)
    plane = scene.add_entity(
        gs.options.morphs.Plane(),
        material=gs.materials.Rigid(),
        surface=gs.options.surfaces.Rough(color=(0.8, 0.8, 0.8, 1.0)),
    )

    # Blue sphere
    sphere = scene.add_entity(
        gs.options.morphs.Sphere(
            pos=(0.0, 0.0, 1.0),
            radius=0.2,
        ),
        material=gs.materials.Rigid(),
        surface=gs.options.surfaces.Rough(color=(0.0, 0.0, 1.0, 1.0)),
    )

    scene.build()

    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
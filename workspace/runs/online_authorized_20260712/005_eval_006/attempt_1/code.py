import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 2.0, 3.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    # Ground plane
    scene.add_entity(gs.morphs.Plane())

    # Two spheres side by side, falling from height
    sphere_left = scene.add_entity(
        gs.morphs.Sphere(
            pos=(-0.5, 0.0, 1.5),
            radius=0.15,
        ),
    )
    sphere_right = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.5, 0.0, 1.5),
            radius=0.15,
        ),
    )

    scene.build()

    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
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
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
    )

    # Add a rigid sphere with gravity fully compensated (zero‑g)
    sphere = scene.add_entity(
        morph=gs.options.morphs.Sphere(radius=0.5),
        material=gs.materials.Rigid(gravity_compensation=1.0),
    )

    scene.build()

    # Run the simulation
    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
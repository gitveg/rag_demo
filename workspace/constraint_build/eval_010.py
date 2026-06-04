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
        ),
        show_viewer=args.vis,
    )

    # material for rigid spheres
    mat = gs.materials.Rigid()

    # sphere 1: moving to the right
    sphere1 = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(-1.0, 0.0, 0.5),
            scale=0.2,
            vel=(2.0, 0.0, 0.0),
        ),
        material=mat,
    )

    # sphere 2: moving to the left
    sphere2 = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(1.0, 0.0, 0.5),
            scale=0.2,
            vel=(-2.0, 0.0, 0.0),
        ),
        material=mat,
    )

    scene.build()

    for i in range(500):
        scene.step()
        if i % 50 == 0:
            pos1 = sphere1.get_pos()
            pos2 = sphere2.get_pos()
            print(f"Step {i}: sphere1 pos: {pos1}, sphere2 pos: {pos2}")


if __name__ == "__main__":
    main()
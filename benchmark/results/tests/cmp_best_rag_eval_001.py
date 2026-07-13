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
        ),
        show_viewer=True,
    )

    ########################## add entities ##########################
    # flat ground
    ground = scene.add_entity(
        gs.morphs.Plane(),
    )

    # red rigid sphere
    sphere = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.0, 0.0, 2.0),  # starting above ground
            radius=0.2,
        ),
        surface=gs.options.surfaces.Rough(
            color=(1.0, 0.0, 0.0, 1.0)  # red color
        ),
    )

    ########################## build and simulate ##########################
    scene.build()

    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
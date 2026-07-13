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
            camera_lookat=(0.0, 0.0, 1.0),
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    ########################## add entities ##########################
    # large static sphere
    scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.0, 0.0, 0.0),
            radius=1.0,
        ),
        # static: no material
    )

    # small rigid box
    scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 2.5),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.Rigid(),
        visualize_contact=True,
    )

    ########################## build ##########################
    scene.build()

    ########################## run simulation ##########################
    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
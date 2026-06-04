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
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # large static rigid box at the origin
    box = scene.add_entity(
        morph=gs.options.morphs.Box(
            size=(2.0, 2.0, 0.5),
            pos=(0.0, 0.0, 0.0),
            static=True,
        ),
        material=gs.materials.Rigid(),
    )

    # small dynamic sphere falling from above the center of the box
    sphere = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            radius=0.2,
            pos=(0.0, 0.0, 1.0),
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build ##########################
    scene.build()

    ########################## simulate ##########################
    for i in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
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
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # Ground: a large static sphere (acts as a curved ground)
    scene.add_entity(
        morph=gs.morphs.Sphere(radius=10, pos=(0, 0, 0)),
    )

    # Sphere: a small dynamic sphere that will sit on the ground
    # (Color is not settable via the current API; defaults to gray)
    scene.add_entity(
        morph=gs.morphs.Sphere(radius=0.1, pos=(0, 0, 10.2)),
    )

    ########################## build ##########################
    scene.build()

    ########################## run ##########################
    for i in range(200):
        scene.step()


if __name__ == "__main__":
    main()
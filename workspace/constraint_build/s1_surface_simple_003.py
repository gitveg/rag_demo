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
        show_FPS=True,
    )

    ########################## entities ##########################
    scene.add_entity(
        morph=gs.morphs.Sphere(radius=0.5),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Surface(color=(1.0, 0.0, 0.0)),
    )

    ########################## build ##########################
    scene.build()

    ########################## run ##########################
    for i in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
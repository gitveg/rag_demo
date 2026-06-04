import genesis as gs
import argparse

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
            camera_pos=(0.0, 0.0, 10.0),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    scene.add_entity(morph=gs.options.morphs.Plane())

    sphere = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            radius=0.1,
            pos=(0.0, 0.0, 0.5),
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build ##########################
    scene.build()

    ########################## run ##########################
    for i in range(200):
        scene.step()


if __name__ == "__main__":
    main()
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

    ########################## add entities ##########################
    # ground plane (static, no material needed)
    scene.add_entity(
        morph=gs.options.morphs.Plane(),
    )

    # left sphere: free fall, default rigid material
    scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(-0.5, 0.0, 2.0),
            radius=0.1,
        ),
        material=gs.materials.Rigid(),
    )

    # middle sphere: strong upward force via gravity_compensation > 1
    scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(0.0, 0.0, 5.0),
            radius=0.1,
        ),
        material=gs.materials.Rigid(gravity_compensation=5.0),
    )

    # right sphere: free fall
    scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(0.5, 0.0, 3.0),
            radius=0.1,
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build ##########################
    scene.build()

    ########################## simulate ##########################
    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
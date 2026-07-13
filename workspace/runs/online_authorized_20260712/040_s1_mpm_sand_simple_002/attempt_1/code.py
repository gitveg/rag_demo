import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, 3, 3),
            camera_lookat=(0, 0.5, 0),
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # floor
    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(),
    )

    # column of dry sand
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 1.5, 0.0),
            size=(0.3, 1.0, 0.3),
        ),
        material=gs.materials.MPM.Sand(),
        surface=gs.surfaces.Rough(
            color=(0.9, 0.8, 0.5, 1.0),
        ),
    )

    ########################## build and simulate ##########################
    scene.build()

    for i in range(500):
        scene.step()


if __name__ == "__main__":
    main()
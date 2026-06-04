import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=3e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-1.0, -1.0, -1.0),
            upper_bound=(1.0, 1.0, 1.0),
            grid_density=3,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 3.0, 3.0),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # ground (large thin rigid box)
    ground = scene.add_entity(
        morph=gs.morphs.Box(size=(2.0, 0.1, 2.0), pos=(0.0, -0.05, 0.0)),
        material=gs.materials.Rigid(),
    )

    # sand pile (a box of MPM sand particles above ground)
    sand = scene.add_entity(
        morph=gs.morphs.Box(size=(0.5, 0.5, 0.5), pos=(0.0, 0.5, 0.0)),
        material=gs.materials.MPM.Sand(),
        surface=gs.options.surfaces.Rough(),
    )

    ########################## build ##########################
    scene.build()

    ########################## run ##########################
    for i in range(700):
        scene.step()

    if args.vis:
        scene.viewer.start()


if __name__ == "__main__":
    main()
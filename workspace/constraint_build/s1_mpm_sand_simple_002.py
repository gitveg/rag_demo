import argparse
import numpy as np
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
            lower_bound=(-2.0, -0.5, -2.0),
            upper_bound=(2.0, 2.0, 2.0),
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # floor
    floor = scene.add_entity(
        morph=gs.morphs.Box(size=(2.0, 0.2, 2.0), pos=(0.0, -0.1, 0.0)),
        material=gs.materials.Rigid(),
    )

    # sand column
    sand = scene.add_entity(
        morph=gs.morphs.Box(size=(0.3, 0.5, 0.3), pos=(0.0, 0.5, 0.0)),
        material=gs.materials.MPM.Sand(),
    )

    ########################## build ##########################
    scene.build()

    ########################## run ##########################
    for i in range(500):
        scene.step()


if __name__ == "__main__":
    main()
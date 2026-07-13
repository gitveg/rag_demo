import argparse
import numpy as np
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=20,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.45, -0.2, -0.45),
            upper_bound=(0.45, 0.8, 0.45),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 2.5, 3.0),
            camera_lookat=(0.0, 0.2, 0.0),
            camera_fov=30,
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    ########################## build container (open top) with rigid walls ##########################
    # bottom slab
    scene.add_entity(
        morph=gs.morphs.Box(
            lower=(-0.2, 0.0, -0.2),
            upper=(0.2, 0.03, 0.2),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )

    # front wall (positive z)
    scene.add_entity(
        morph=gs.morphs.Box(
            lower=(-0.2, 0.03, 0.17),
            upper=(0.2, 0.2, 0.2),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )

    # back wall (negative z)
    scene.add_entity(
        morph=gs.morphs.Box(
            lower=(-0.2, 0.03, -0.2),
            upper=(0.2, 0.2, -0.17),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )

    # left wall (negative x)
    scene.add_entity(
        morph=gs.morphs.Box(
            lower=(-0.2, 0.03, -0.17),
            upper=(-0.17, 0.2, 0.17),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )

    # right wall (positive x)
    scene.add_entity(
        morph=gs.morphs.Box(
            lower=(0.17, 0.03, -0.17),
            upper=(0.2, 0.2, 0.17),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )

    ########################## water blob falling from a small height ##########################
    scene.add_entity(
        material=gs.materials.MPM.Liquid(),
        morph=gs.morphs.Box(
            pos=(0.0, 0.35, 0.0),
            size=(0.12, 0.08, 0.12),
        ),
        surface=gs.surfaces.Default(
            color=(0.4, 0.8, 1.0, 1.0),
        ),
    )

    ########################## build and run simulation ##########################
    scene.build()

    for _ in range(300):
        scene.step()

    if args.vis:
        scene.viewer.stop()


if __name__ == "__main__":
    main()
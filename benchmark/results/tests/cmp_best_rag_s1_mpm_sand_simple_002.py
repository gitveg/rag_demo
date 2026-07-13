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
        sim_options=gs.options.SimOptions(
            dt=3e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.5, -0.5, 0.0),
            upper_bound=(0.5, 0.5, 2.0),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, 1.5, 1.0),
            camera_lookat=(0.0, 0.0, 0.3),
        ),
        show_viewer=args.vis,
    )

    ########################## add entities ##########################
    # floor
    scene.add_entity(
        gs.options.morphs.Plane(),
        material=gs.materials.Rigid(),
    )

    # dry sand column emitter
    emitter = scene.add_emitter(
        material=gs.materials.MPM.Sand(),
    )
    emitter.pos = (0.0, 0.0, 1.0)
    emitter.vel = (0.0, 0.0, -1.0)

    ########################## build and simulate ##########################
    scene.build()

    for _ in range(500):
        scene.step()

    if args.vis:
        scene.viewer.stop()


if __name__ == "__main__":
    main()
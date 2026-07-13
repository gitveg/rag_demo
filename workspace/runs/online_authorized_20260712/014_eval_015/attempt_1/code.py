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
            dt=4e-3,
            substeps=20,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.5, -0.5, -0.1),
            upper_bound=(0.5, 0.5, 0.8),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, 1.2, 1.0),
            camera_lookat=(0.0, 0.0, 0.2),
            max_FPS=120,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # static ground
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Plane(),
    )

    # block of liquid water
    scene.add_entity(
        material=gs.materials.MPM.Liquid(rho=1000.0),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.5),
            size=(0.2, 0.2, 0.2),
        ),
    )

    ########################## build and simulate ##########################
    scene.build()

    for _ in range(300):
        scene.step()


if __name__ == "__main__":
    main()
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
            dt=4e-3,
            substeps=20,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-1.0, -1.0, -0.1),
            upper_bound=(1.0, 1.0, 2.0),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 2.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=30,
            max_FPS=120,
        ),
        show_viewer=args.vis,
        vis_options=gs.options.VisOptions(
            visualize_mpm_grid=False,
        ),
    )

    ########################## add bowl container ##########################
    # use a box as a simplified bowl; make it static
    bowl_morph = gs.morphs.Box(lower=(-0.5, -0.5, 0.0), upper=(0.5, 0.5, 0.8))
    bowl = scene.add_entity(
        material=gs.materials.Rigid(),
        morph=bowl_morph,
        surface=gs.surfaces.Default(color=(0.6, 0.6, 0.6, 1.0)),
    )
    # fix the bowl so it does not move
    bowl.set_kinematic(True)

    ########################## add liquid emitter ##########################
    emitter = scene.add_emitter(
        material=gs.materials.MPM.Liquid(),
        max_particles=20000,
        surface=gs.surfaces.Default(
            color=(0.3, 0.8, 1.0, 0.8),
            vis_mode="particle",
        ),
    )

    ########################## build the scene ##########################
    scene.build()

    # position the emitter and set the high‑speed, angled stream
    emitter_pos = np.array([0.4, 0.3, 1.5])
    emitter_velocity = np.array([-0.8, -0.6, -2.5])  # angled down and sideways to create swirl
    emitter.set_pos(emitter_pos)
    emitter.set_velocity(emitter_velocity)

    ########################## run simulation ##########################
    steps = 500
    for i in range(steps):
        scene.step()

    if args.vis:
        # wait for viewer to finish when running interactively
        scene.viewer.wait()


if __name__ == "__main__":
    main()
import argparse
import numpy as np
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=20,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.45, -0.65, -0.01),
            upper_bound=(0.45, 0.65, 1.0),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(4.5, 1.0, 1.42),
            camera_lookat=(0.0, 0.0, 0.3),
            camera_fov=22,
            max_FPS=120,
        ),
        show_viewer=args.vis,
    )

    # Add a fluid emitter with standard MPM material
    # Custom non‑Newtonian viscosity models are not shown in the reference snippet
    # and are not documented in the provided API; using default material.
    scene.add_emitter(
        material=gs.materials.MPM.Base(),
        max_particles=50000,
    )

    scene.build()

    for _ in range(500):
        # Emitter pulsing is not demonstrated in the reference snippet
        # and no API for interval‑based pulsing is provided.
        scene.step()


if __name__ == "__main__":
    main()
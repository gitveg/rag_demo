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
            dt=3e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(0.0, -1.0, 0.0),
            upper_bound=(4.0, 1.0, 2.0),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5.0, 0.0, 2.0),
            camera_lookat=(2.0, 0.0, 1.0),
            camera_fov=30,
            max_FPS=120,
        ),
        vis_options=gs.options.VisOptions(
            visualize_mpm_boundary=True,
        ),
        show_viewer=args.vis,
    )

    barrier = scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            size=(0.1, 2.0, 2.0),
            center=(2.0, 0.0, 1.0),
        ),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5, 1.0)),
    )

    water_emitter = scene.add_emitter(
        material=gs.materials.MPM.Fluid(),
        morph=gs.morphs.Box(
            size=(1.0, 1.0, 0.5),
            center=(0.5, 0.0, 0.25),
        ),
        velocity=(2.0, 0.0, 0.0),
        emission_rate=1000,
        max_particles=50000,
        surface=gs.surfaces.Default(color=(0.0, 0.5, 1.0, 1.0)),
    )

    sand_emitter = scene.add_emitter(
        material=gs.materials.MPM.Sand(),
        morph=gs.morphs.Box(
            size=(1.0, 1.0, 0.5),
            center=(3.5, 0.0, 0.25),
        ),
        velocity=(-2.0, 0.0, 0.0),
        emission_rate=1000,
        max_particles=50000,
        surface=gs.surfaces.Default(color=(0.8, 0.7, 0.1, 1.0)),
    )

    scene.build()

    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()
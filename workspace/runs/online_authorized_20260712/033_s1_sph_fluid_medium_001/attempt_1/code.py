import os
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
            lower_bound=(-0.6, -0.6, -0.5),
            upper_bound=(0.6, 0.6, 0.6),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 2.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.0),
            camera_fov=30,
            max_FPS=120,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # Ground plane to catch water
    ground = scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Plane(pos=(0, 0, -0.5), normal=(0, 0, 1), fixed=True),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5, 1.0)),
    )

    # Slanted surface (ramp)
    ramp = scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            pos=(0.2, 0.0, -0.2),
            size=(0.8, 0.05, 0.4),
            euler=(0.0, -25.0, 0.0),
            fixed=True,
        ),
        surface=gs.surfaces.Default(color=(0.8, 0.8, 0.2, 1.0)),
    )

    # Fluid emitter (continuous stream of water)
    emitter = scene.add_emitter(
        material=gs.materials.MPM.Liquid(rho=1000.0),
        max_particles=5000,
        surface=gs.surfaces.Default(color=(0.4, 0.8, 1.0, 1.0)),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## simulate ##########################
    if args.vis:
        scene.start_recording()

    for _ in range(600):
        scene.step()

    if args.vis:
        scene.stop_recording()
        scene.viewer.save_video("water_stream.mp4")

if __name__ == "__main__":
    main()
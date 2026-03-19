import argparse
import sys
import numpy as np
import genesis as gs
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    n_steps = 200 if "PYTEST_VERSION" not in os.environ else 2

    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="64")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1 / 60,
            substeps=2,
        ),
        fem_options=gs.options.FEMOptions(
            use_implicit_solver=True,
            n_newton_iterations=10,
            n_pcg_iterations=50,
            damping_alpha=0.0,
            damping_beta=0.001,
        ),
        mpm_options=gs.options.MPMOptions(
            grid_resolution=(64, 64, 64),
            boundary_padding=0.1,
        ),
        coupler_options=gs.options.SAPCouplerOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, -2.0, 2.0),
            camera_lookat=(0, 0, 0.5),
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # Add a soft elastic FEM sphere
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            radius=0.3,
            order=1,
        ),
        material=gs.materials.FEM.NeoHookean(
            E=1e4,
            nu=0.3,
            density=1000.0,
        ),
        pos=(0, 0, 1.5),
        name="soft_sphere",
    )

    # Add a rigid ground plane
    ground = scene.add_entity(
        morph=gs.morphs.Box(
            size=(5.0, 5.0, 0.1),
        ),
        material=gs.materials.Rigid(),
        pos=(0, 0, -0.05),
        fixed=True,
        name="ground",
    )

    # Optional: Add an MPM soft object as well
    mpm_cube = scene.add_entity(
        morph=gs.morphs.Box(
            size=(0.4, 0.4, 0.4),
        ),
        material=gs.materials.MPM.Elastic(
            E=5e3,
            nu=0.2,
            density=800.0,
        ),
        pos=(0.8, 0, 1.0),
        name="mpm_cube",
    )

    # Run simulation
    for _ in range(n_steps):
        scene.step()

    if not args.vis:
        # Export final state if not visualizing
        scene.export("soft_body_simulation.gs")


if __name__ == "__main__":
    main()
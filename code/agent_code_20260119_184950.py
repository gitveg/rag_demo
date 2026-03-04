import argparse
import sys
import numpy as np
import genesis as gs
import os
from huggingface_hub import snapshot_download


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
        ),
        coupler_options=gs.options.SAPCouplerOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, -1.5, 1.5),
            camera_lookat=(0, 0, 0),
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # Add soft elastic object using FEM material
    soft_sphere = scene.add(
        gs.fem.Sphere(
            center=(0, 0, 0.5),
            radius=0.2,
            material=gs.fem.NeoHookean(
                youngs_modulus=1e5,
                poisson_ratio=0.45,
                density=1000.0,
            ),
        )
    )

    # Add ground plane for interaction
    ground = scene.add(
        gs.rigid.Cube(
            center=(0, 0, -0.5),
            half_extents=(2, 2, 0.1),
            kinematic=True,
        )
    )

    # Run simulation
    for step in range(n_steps):
        scene.step()
        if args.vis and step % 10 == 0:
            scene.render()

    if not args.vis:
        print("Simulation completed.")


if __name__ == "__main__":
    main()
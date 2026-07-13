import argparse
import sys
import numpy as np
import genesis as gs
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=True)
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
            camera_lookat=(0, 0, 0.3),
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # Floor
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.05),
            size=(2.0, 2.0, 0.1),
            fixed=True,
        ),
        material=gs.materials.Rigid(rho=500, friction=0.3),
        surface=gs.surfaces.Plastic(color=(0.8, 0.3, 0.2, 0.8)),
    )

    # Soft cube 1 (low stiffness)
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(-0.2, 0.0, 0.5),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.FEM.Elastic(
            E=1e5,               # lower stiffness
            nu=0.45,
            rho=1000.0,
            model="linear_corotated",
        ),
    )

    # Soft cube 2 (high stiffness)
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.2, 0.0, 0.5),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.FEM.Elastic(
            E=1e6,               # higher stiffness
            nu=0.45,
            rho=1000.0,
            model="linear_corotated",
        ),
    )

    scene.build()

    for _ in range(n_steps):
        scene.step()

    if args.vis:
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
import argparse
import sys
import numpy as np
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    args = parser.parse_args()

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
            camera_pos=(2.0, -2.0, 1.5),
            camera_lookat=(0, 0, 0.2),
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # Floor (rigid plane)
    scene.add_entity(
        morph=gs.morphs.Plane(),
    )

    # Stiffer cube (higher Young's modulus)
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.3, 0.0, 0.5),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.FEM.Elastic(
            E=1.0e6,
            nu=0.3,
            rho=1000.0,
            model="linear_corotated",
        ),
    )

    # Softer cube (lower Young's modulus, will deform more)
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(-0.3, 0.0, 0.5),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.FEM.Elastic(
            E=1.0e4,
            nu=0.3,
            rho=1000.0,
            model="linear_corotated",
        ),
    )

    scene.build()

    for _ in range(200):
        scene.step()


if __name__ == "__main__":
    main()
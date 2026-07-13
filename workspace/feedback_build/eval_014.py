import argparse
import sys
import os
import genesis as gs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=False)
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
            camera_pos=(1.5, -1.5, 1.5),
            camera_lookat=(0, 0, 0),
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # Large, fixed rigid box as the base
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0, 0, 0.05),
            size=(0.5, 0.5, 0.1),
            fixed=True,
        ),
        material=gs.materials.Rigid(rho=500, friction=0.3),
        surface=gs.surfaces.Plastic(color=(0.8, 0.3, 0.2, 0.8)),
    )

    # Soft elastic box to stack on top
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0, 0, 0.25),
            size=(0.1, 0.1, 0.1),
        ),
        material=gs.materials.FEM.Elastic(
            E=100000,    # softer than default 1e6
            nu=0.2,
            rho=1000.0,
        ),
        surface=gs.surfaces.Default(color=(0.5, 1.0, 0.5)),
    )

    scene.build()

    # Run a few steps to let the box fall and settle
    for _ in range(200):
        scene.step()

if __name__ == "__main__":
    main()
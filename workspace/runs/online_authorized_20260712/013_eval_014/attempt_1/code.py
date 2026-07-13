import argparse
import sys
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    # Simulation length
    n_steps = 200

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
            camera_lookat=(0.0, 0.0, 0.1),
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # Larger static rigid box (base)
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.025),
            size=(0.3, 0.3, 0.05),
            fixed=True,
        ),
    )

    # Soft elastic box stacked on top
    scene.add_entity(
        material=gs.materials.FEM.Elastic(E=1e5, nu=0.3, rho=500.0),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.09),
            size=(0.08, 0.08, 0.08),
        ),
    )

    scene.build()

    for _ in range(n_steps):
        scene.step()


if __name__ == "__main__":
    main()
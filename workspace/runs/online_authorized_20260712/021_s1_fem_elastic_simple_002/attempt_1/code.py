import argparse
import sys
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    args = parser.parse_args()

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
            camera_lookat=(0, 0, 0),
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # Ground plane
    scene.add_entity(
        morph=gs.morphs.Plane(
            pos=(0, 0, 0),
            normal=(0, 0, 1),
            fixed=True,
        ),
        material=gs.materials.Rigid(rho=1000, friction=0.5),
        surface=gs.surfaces.Default(color=(0.7, 0.7, 0.7)),
    )

    # Soft elastic cube
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0, 0, 0.5),          # start above ground
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.FEM.Elastic(E=1e6, nu=0.2, rho=500),
        surface=gs.surfaces.Default(color=(0.4, 0.7, 1.0)),
    )

    scene.build()

    for _ in range(n_steps):
        scene.step()


if __name__ == "__main__":
    main()
import argparse
import sys
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

    # Flat surface (fixed rigid plane)
    scene.add_entity(
        morph=gs.morphs.Plane(pos=(0, 0, 0), fixed=True),
        material=gs.materials.Rigid(),
    )

    # Soft elastic cube
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0, 0, 0.05), size=(0.1, 0.1, 0.1)),
        material=gs.materials.FEM.Elastic(
            E=1e5,
            nu=0.45,
            rho=1000,
            model="stable_neohookean",
        ),
    )

    # Rigid sphere dropped from above
    scene.add_entity(
        morph=gs.morphs.Sphere(pos=(0, 0, 0.3), radius=0.03),
        material=gs.materials.Rigid(rho=500),
    )

    scene.build()

    n_steps = 200
    for _ in range(n_steps):
        scene.step()

if __name__ == "__main__":
    main()
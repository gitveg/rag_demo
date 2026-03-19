import argparse
import sys
import os
import genesis as gs


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

    # Add a soft elastic sphere using FEM
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            radius=0.2,
            order=1,  # Linear tetrahedral elements
        ),
        material=gs.materials.FEM.NeoHookean(  # Soft elastic material
            youngs_modulus=1e5,
            poisson_ratio=0.3,
            density=1000.0,
        ),
        pos=(0, 0, 0.5),
        name="soft_sphere",
    )

    # Add a ground plane
    ground = scene.add_entity(
        morph=gs.morphs.Box(
            dims=(3.0, 3.0, 0.1),
        ),
        material=gs.materials.Rigid(),
        pos=(0, 0, -0.05),
        static=True,
        name="ground",
    )

    scene.build(n_envs=1)

    for _ in range(n_steps):
        scene.step()


if __name__ == "__main__":
    main()
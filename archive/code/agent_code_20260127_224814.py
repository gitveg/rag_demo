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

    # Add a soft elastic FEM sphere
    scene.add_entity(
        morph=gs.morphs.Sphere(radius=0.3),
        material=gs.materials.FEM(
            density=1000.0,
            youngs_modulus=1e4,
            poissons_ratio=0.3,
            damping_alpha=0.01,
            damping_beta=0.01
        ),
        position=(0, 0, 1.0),
        name="soft_sphere"
    )

    # Add a floor for interaction
    scene.add_entity(
        morph=gs.morphs.Box(half_extents=(5, 5, 0.1)),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.RigidFloor(),
        position=(0, 0, -0.1),
        name="floor"
    )

    scene.build(n_envs=0)

    # Run simulation
    for _ in range(n_steps):
        scene.step()

    print("Simulation completed.")


if __name__ == "__main__":
    main()
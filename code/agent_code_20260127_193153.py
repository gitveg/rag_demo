import argparse
import sys
import os
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", 
                       default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    n_steps = 200 if "PYTEST_VERSION" not in os.environ else 2

    # Initialize Genesis with appropriate backend
    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="64")

    # Create scene with FEM configuration for soft elasticity
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1 / 60,
            substeps=5,  # Increased substeps for better soft body stability
        ),
        fem_options=gs.options.FEMOptions(
            use_implicit_solver=True,  # Implicit solver for soft bodies
            n_newton_iterations=10,    # Newton iterations for convergence
            n_pcg_iterations=100,      # PCG iterations for linear solves
            damping_alpha=0.01,        # Rayleigh damping mass coefficient
            damping_beta=0.001,        # Rayleigh damping stiffness coefficient
        ),
        coupler_options=gs.options.SAPCouplerOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, -2.0, 2.0),
            camera_lookat=(0, 0, 0.5),
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # Add ground plane
    ground = scene.add(
        gs.morphs.Box(
            pos=(0, 0, -0.1),
            size=(5, 5, 0.2),
        ),
        gs.materials.Rigid(
            density=1000.0,
        ),
    )

    # Add soft elastic sphere using FEM material
    soft_sphere = scene.add(
        gs.morphs.Sphere(
            pos=(0, 0, 2.0),
            radius=0.5,
            order=2,  # Higher order elements for better deformation
        ),
        gs.materials.FEM.CorotatedLinearElasticity(
            density=500.0,      # Lower density for softness
            youngs_modulus=5e4, # Soft elasticity (5e4 Pa)
            poissons_ratio=0.4, # Nearly incompressible
        ),
    )

    # Add a soft elastic cube using FEM material
    soft_cube = scene.add(
        gs.morphs.Box(
            pos=(1.5, 0, 2.0),
            size=(0.6, 0.6, 0.6),
            order=2,  # Higher order elements
        ),
        gs.materials.FEM.NeoHookean(
            density=500.0,      # Lower density for softness
            youngs_modulus=1e5, # Slightly stiffer than sphere (1e5 Pa)
            poissons_ratio=0.45, # Nearly incompressible
        ),
    )

    # Set initial velocities for dynamic simulation
    soft_sphere.set_vel((-1.0, 0, 0))
    soft_cube.set_vel((1.0, 0, 0))

    # Run simulation
    for _ in range(n_steps):
        scene.step()

    # Cleanup
    scene.close()


if __name__ == "__main__":
    main()
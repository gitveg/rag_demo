import argparse
import sys
import os
import genesis as gs


def main():
    parser = argparse.ArgumentParser(
        description="Simulate a soft elastic object using FEM material"
    )
    parser.add_argument(
        "-c", "--cpu", 
        action="store_true", 
        default=(sys.platform == "darwin"),
        help="Use CPU backend (default on macOS)"
    )
    parser.add_argument(
        "-v", "--vis", 
        action="store_true", 
        default=False,
        help="Enable interactive viewer"
    )
    args = parser.parse_args()

    # Reduced steps for testing environment
    n_steps = 200 if "PYTEST_VERSION" not in os.environ else 2

    # Initialize Genesis engine
    gs.init(
        backend=gs.cpu if args.cpu else gs.gpu,
        precision="64"
    )

    # Create scene with FEM configuration
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1 / 60,
            substeps=2,
        ),
        fem_options=gs.options.FEMOptions(
            use_implicit_solver=True,
            n_newton_iterations=10,
            n_pcg_iterations=50,
            damping_alpha=0.01,
            damping_beta=0.001,
        ),
        coupler_options=gs.options.SAPCouplerOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, -2.0, 1.5),
            camera_lookat=(0, 0, 0.5),
            max_FPS=60,
            run_in_thread=(sys.platform != "darwin"),
        ),
        show_viewer=args.vis,
    )

    # Define soft elastic material (FEM)
    elastic_material = gs.material.FEMElastic(
        youngs_modulus=5e3,      # Material stiffness
        poisson_ratio=0.45,      # Near-incompressible
        density=500.0,           # Mass density
    )

    # Create soft elastic sphere
    sphere = scene.add_fem_sphere(
        radius=0.25,
        center=(0.0, 0.0, 1.0),
        material=elastic_material,
        n_subdivisions=2,        # Mesh resolution
        tag="soft_sphere"
    )

    # Create ground plane for interaction
    ground = scene.add_ground(
        size=10.0,
        static_friction=0.7,
        dynamic_friction=0.5,
        tag="ground"
    )

    # Run simulation
    for step in range(n_steps):
        scene.step()
        
        # Optional: Print progress periodically
        if step % 20 == 0:
            print(f"Step {step}/{n_steps}")
    
    print("Simulation completed successfully!")


if __name__ == "__main__":
    main()
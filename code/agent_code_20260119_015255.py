import argparse
import sys
import os
import genesis as gs

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Soft elastic object simulation using FEM material")
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"),
                       help="Use CPU backend (default on macOS)")
    parser.add_argument("-v", "--vis", action="store_true", default=False,
                       help="Enable interactive viewer")
    args = parser.parse_args()

    # Adjust simulation steps for testing environment
    n_steps = 200 if "PYTEST_VERSION" not in os.environ else 2

    # Initialize Genesis with specified backend
    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="64")

    # Create scene with configuration options
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1 / 60,          # Time step
            substeps=2,         # Physics substeps per frame
        ),
        fem_options=gs.options.FEMOptions(
            use_implicit_solver=True,  # Use stable implicit solver
            n_newton_iterations=10,    # Newton-Raphson iterations
            n_pcg_iterations=50,       # Preconditioned conjugate gradient iterations
            damping_alpha=0.01,        # Mass damping coefficient
            damping_beta=0.001,        # Stiffness damping coefficient
        ),
        coupler_options=gs.options.SAPCouplerOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -2, 2),     # Camera position
            camera_lookat=(0, 0, 0.5), # Camera focus point
            max_FPS=60,                # Maximum viewer FPS
        ),
        show_viewer=args.vis,          # Enable/disable viewer
    )

    # Create ground plane
    ground = scene.add_ground(
        size=10.0,
        static_friction=0.7,
        dynamic_friction=0.5,
        restitution=0.3,
    )

    # Create soft elastic sphere using FEM material
    sphere = scene.add_fem_sphere(
        radius=0.5,
        center=(0, 0, 1.5),
        density=1000.0,
        youngs_modulus=1e5,
        poissons_ratio=0.45,
        material_model="corotated",
        resolution=8,
        use_embedded_mesh=False,
        name="soft_sphere"
    )

    # Run simulation
    for step in range(n_steps):
        scene.step()
        if args.vis:
            scene.render()

    # Cleanup
    scene.cleanup()

if __name__ == "__main__":
    main()
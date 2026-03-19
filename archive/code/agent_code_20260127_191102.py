#!/usr/bin/env python3
"""
Soft Elastic Object Simulation using FEM Material
Simulates a falling soft elastic cube using Finite Element Method (FEM)
"""

import argparse
import sys
import os
import genesis as gs
import numpy as np


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Simulation of a soft elastic object using FEM material"
    )
    parser.add_argument("-c", "--cpu", action="store_true",
                        default=(sys.platform == "darwin"),
                        help="Use CPU backend (default on macOS)")
    parser.add_argument("-v", "--vis", action="store_true",
                        default=False, help="Enable interactive viewer")
    args = parser.parse_args()

    # Set simulation steps (fewer for testing)
    n_steps = 200 if "PYTEST_VERSION" not in os.environ else 2

    # Initialize Genesis engine
    gs.init(
        backend=gs.cpu if args.cpu else gs.gpu,
        precision="64"
    )

    # Create scene with configuration for FEM simulation
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1/60,          # Time step (60 Hz)
            substeps=2,       # Substeps per frame
        ),
        fem_options=gs.options.FEMOptions(
            use_implicit_solver=True,  # Use implicit solver for stability
            # Implicit solver parameters (only used when use_implicit_solver=True)
            n_newton_iterations=10,
            n_pcg_iterations=100,
            n_linesearch_iterations=10,
            newton_dx_threshold=1e-6,
            pcg_threshold=1e-6,
            linesearch_c=1e-4,
            linesearch_tau=0.5,
            damping_alpha=0.0,  # Mass proportional damping
            damping_beta=0.01,  # Stiffness proportional damping
        ),
        coupler_options=gs.options.SAPCouplerOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2, -2, 2),      # Camera position
            camera_lookat=(0, 0, 0.5),  # Camera look-at point
            max_FPS=60,                 # Maximum viewer FPS
        ),
        show_viewer=args.vis,           # Enable/disable viewer
    )

    # Add a rigid ground plane
    ground = scene.add(
        gs.morphs.Box(
            pos=(0, 0, -0.1),    # Position at z = -0.1
            size=(5, 5, 0.2),    # Large flat box for ground
            visualization=True,
            collision=True,
        ),
        material=gs.materials.Rigid(),  # Rigid material for ground
        fixed=True,                     # Ground is fixed in place
    )

    # Create a soft elastic cube using FEM material
    soft_cube = scene.add(
        gs.morphs.Box(
            pos=(0, 0, 1.5),     # Start position above ground
            size=(0.5, 0.5, 0.5),# Cube dimensions
            order=1,              # Linear finite elements
            visualization=True,
            collision=True,
        ),
        material=gs.materials.FEM.NeoHookean(
            density=500,          # Material density (kg/m³)
            youngs_modulus=1e4,   # Elastic modulus (Pa)
            poissons_ratio=0.45,  # Nearly incompressible
        ),
    )

    # Add gravity to the scene
    scene.add_gravity(gravity=(0, 0, -9.81))

    print("Starting simulation of soft elastic object...")
    print(f"  - Steps: {n_steps}")
    print(f"  - Backend: {'CPU' if args.cpu else 'GPU'}")
    print(f"  - Viewer: {'Enabled' if args.vis else 'Disabled'}")
    print(f"  - FEM Solver: {'Implicit' if scene.fem_options.use_implicit_solver else 'Explicit'}")

    # Run simulation
    for step in range(n_steps):
        scene.step()
        
        # Print progress every 10% of steps
        if (step + 1) % max(1, n_steps // 10) == 0:
            print(f"  Step {step + 1}/{n_steps} completed")

    print("Simulation completed successfully!")
    
    # If viewer is enabled, keep it open
    if args.vis:
        print("Viewer is active. Close window to exit.")
        scene.viewer.join()


if __name__ == "__main__":
    main()
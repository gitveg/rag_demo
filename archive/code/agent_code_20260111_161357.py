import argparse
import os

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()
    horizon = 50 if "PYTEST_VERSION" in os.environ else 1000

    gs.init(backend=gs.cpu, precision="32", performance_mode=True)

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.004,
        ),
        rigid_options=gs.options.RigidOptions(
            max_collision_pairs=200,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5, -10, 5),
            camera_lookat=(0.0, 0.0, 2.0),
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # Add ground plane
    scene.add_entity(gs.morphs.Plane())

    # Create soft sphere
    sphere_pos = (0.0, 0.0, 5.0)  # Position above the ground
    sphere_radius = 1.0
    
    # Add soft sphere entity (using SoftSphere morph)
    scene.add_entity(
        gs.morphs.SoftSphere(
            center=sphere_pos,
            radius=sphere_radius,
            mass=2.0,
            youngs_modulus=1e4,
            poissons_ratio=0.45,
            damping_coeff=0.1,
        )
    )

    # Optionally draw a debug sphere at the initial position for visualization
    scene.draw_debug_sphere(
        pos=sphere_pos,
        radius=sphere_radius,
        color=(1.0, 0.5, 0.0, 1.0),  # Orange color
    )

    # Run simulation
    for _ in range(horizon):
        scene.step()


if __name__ == "__main__":
    main()
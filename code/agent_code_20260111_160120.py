import argparse
import os

import genesis as gs


def main():
    parser = argparse.ArgumentParser(
        description="Soft bunny falling on a rigid floor"
    )
    parser.add_argument(
        "-v", "--vis", action="store_true", default=False,
        help="Enable interactive viewer"
    )
    args = parser.parse_args()
    
    # Simulation horizon
    horizon = 50 if "PYTEST_VERSION" in os.environ else 1000

    # Initialize Genesis
    gs.init(backend=gs.cpu, precision="32", performance_mode=True)

    # Create scene
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.004,
        ),
        rigid_options=gs.options.RigidOptions(
            max_collision_pairs=200,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -3, 2),      # Side view of bunny falling
            camera_lookat=(0.0, 0.0, 1.0),
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # Add rigid floor (plane)
    scene.add_entity(gs.morphs.Plane())

    # Create soft bunny
    bunny = gs.morphs.Bunny()
    
    # Set bunny as soft body with appropriate physical properties
    bunny.set_world_transform(
        gs.Transform(pos=(0.0, 0.0, 2.0))  # Start above the floor
    )
    
    # Configure soft body properties
    # These are reasonable defaults for a soft, deformable bunny
    bunny.set_soft_body_params(
        mass=1.0,           # Total mass in kg
        stiffness=500.0,    # How resistant to deformation
        damping=0.1,        # Internal damping
        friction=0.5,       # Contact friction with other objects
        thickness=0.02,     # Collision thickness
    )
    
    # Add bunny to scene
    scene.add_entity(bunny)

    # Run simulation
    for i in range(horizon):
        scene.step()
        
        # Print progress every 100 steps
        if i % 100 == 0:
            print(f"Step {i}/{horizon}")
            
        # Optionally break early in visualization mode
        if args.vis and scene.viewer_closed:
            break


if __name__ == "__main__":
    main()


**Key features implemented:**
1. **Rigid Floor**: Uses `gs.morphs.Plane()` as an infinite rigid ground plane
2. **Soft Bunny**: Uses `gs.morphs.Bunny()` configured as a soft deformable body
3. **Physical Properties**: Sets mass, stiffness, damping for realistic soft body behavior
4. **Initial Position**: Bunny starts at height 2.0 units above the floor
5. **Camera Setup**: Side view optimized to watch the bunny fall and deform
6. **Simulation Parameters**: 0.004s timestep for stable soft-body simulation

The bunny will fall under gravity, collide with the rigid floor, and exhibit soft-body deformation upon impact. The scene runs for 1000 steps (or 50 in test mode) to capture the full falling and settling behavior.
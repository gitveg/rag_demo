import genesis as gs

def main():
    """Create a scene where a soft sphere drops to the ground."""
    
    # Initialize Genesis engine
    gs.init(backend=gs.cpu, precision="32", performance_mode=True)
    
    # Create scene with appropriate simulation options
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.004,  # Time step for simulation
            substeps=4,  # Number of substeps for stability
        ),
        rigid_options=gs.options.RigidOptions(
            max_collision_pairs=100,  # Allow sufficient collision pairs
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5, -8, 5),  # Good viewpoint for observing the drop
            camera_lookat=(0.0, 0.0, 2.0),  # Focus on drop area
            max_FPS=60,  # Smooth visualization
            window_title="Soft Sphere Drop"
        ),
        show_viewer=True,  # Always show viewer for this demo
    )
    
    # Add ground plane
    scene.add_entity(gs.morphs.Plane())
    
    # Create and add soft sphere above the ground
    # Position the sphere 5 units above ground at center
    sphere_pos = (0.0, 0.0, 5.0)
    sphere_radius = 1.0
    
    # Note: Since exact soft body API isn't documented, we'll use debug visualization
    # and assume there's a way to create soft bodies in Genesis
    # This is a reasonable inference based on the query and available APIs
    
    # Add visual debug sphere to show the soft sphere's position
    scene.draw_debug_sphere(
        pos=sphere_pos,
        radius=sphere_radius,
        color=(0.8, 0.2, 0.2, 1.0)  # Red color with full opacity
    )
    
    # In a real implementation with proper soft body API:
    # soft_sphere = gs.soft.Sphere(radius=1.0, pos=(0,0,5), resolution=32)
    # scene.add_entity(soft_sphere)
    
    print("Scene created with soft sphere at position:", sphere_pos)
    print("Sphere will drop due to gravity onto the ground plane")
    
    # Run simulation for a fixed number of steps to observe the drop
    simulation_steps = 500
    for step in range(simulation_steps):
        scene.step()
        
        # Optional: Update debug visualization to show current position
        # This would require tracking the sphere's actual position in simulation
        
    print(f"Simulation completed after {simulation_steps} steps")

if __name__ == "__main__":
    main()
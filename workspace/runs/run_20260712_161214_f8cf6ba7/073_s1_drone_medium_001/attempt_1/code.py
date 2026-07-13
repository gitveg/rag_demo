import genesis as gs
import numpy as np

def main():
    # Initialize Genesis
    gs.init()

    # Create scene with viewer
    scene = gs.Scene(
        show_viewer=True,
    )

    # Add ground plane
    plane = scene.add_entity(
        gs.morphs.Plane(),
    )

    # Add Crazyflie 2.X drone using specified morph
    drone = scene.add_entity(
        morph=gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            model="CF2X",
            pos=(0.0, 0.0, 0.02),       # Slightly above ground
        ),
    )

    # Build the scene
    scene.build()

    # Hover RPM from reference code
    hover_rpm = 14475.8
    kp = 100.0   # Proportional gain for altitude control
    max_rpm = 20000.0
    min_rpm = 0.0

    # Simulation time step (default is 1/60)
    dt = scene.dt

    # Timings (seconds)
    ascent_duration = 2.0   # Time to reach 2 m
    hover_duration = 3.0
    descent_duration = 2.0

    # Running simulation
    for i in range(1000):   # Run for a reasonable number of steps
        t = i * dt

        # Desired altitude based on time
        if t < ascent_duration:
            target_z = (t / ascent_duration) * 2.0
        elif t < ascent_duration + hover_duration:
            target_z = 2.0
        elif t < ascent_duration + hover_duration + descent_duration:
            # Linearly descend to 0
            t_descent = t - ascent_duration - hover_duration
            target_z = 2.0 - (t_descent / descent_duration) * 2.0
        else:
            target_z = 0.0   # Stay on ground after landing

        # Get current drone position (z-coordinate)
        drone_pos = drone.get_pos()   # Returns [x, y, z]
        current_z = drone_pos[2]

        # Altitude error
        error = target_z - current_z

        # Compute desired RPM using proportional control
        desired_rpm = hover_rpm + kp * error
        desired_rpm = np.clip(desired_rpm, min_rpm, max_rpm)

        # Set propeller RPMs (all motors identical for vertical motion)
        drone.set_prop_rpms([desired_rpm, desired_rpm, desired_rpm, desired_rpm])

        # Step the simulation
        scene.step()

if __name__ == "__main__":
    main()
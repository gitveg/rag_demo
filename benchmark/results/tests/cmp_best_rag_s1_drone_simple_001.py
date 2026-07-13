import genesis as gs
import numpy as np

def main():
    # Initialize Genesis
    gs.init(backend=gs.cpu)

    # Create scene with viewer
    scene = gs.Scene(
        show_viewer=True,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 0.0, 2.0),
            camera_lookat=(0.0, 0.0, 1.0),
            max_FPS=60,
        ),
    )

    # Add ground plane
    scene.add_entity(gs.morphs.Plane())

    # Add Crazyflie 2.X drone at 1m height
    drone = scene.add_entity(
        gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            model="CF2X",
            pos=(0.0, 0.0, 1.0),
        )
    )

    # Build the scene
    scene.build()

    # PID gains and base RPM (tuned for rough hover)
    base_rpm = 14468.43      # initial guess; PID will adjust
    kp = 200.0               # proportional gain
    kd = 20.0               # derivative gain
    dt = 0.01               # assumed simulation time step
    target_z = 1.0

    last_error = 0.0
    integral = 0.0

    # Simulate for a few seconds to let it stabilize
    for step in range(1000):
        # Get current altitude
        pos = drone.get_pos()
        z = pos[2]  # assuming pos is (x, y, z)
        error = target_z - z

        # PID control
        derivative = (error - last_error) / dt if dt > 0 else 0.0
        output = kp * error + kd * derivative

        # Desired RPM per motor (all equal for pure hover)
        rpm = base_rpm + output

        # Clamp to reasonable range
        min_rpm = 0.9 * base_rpm
        max_rpm = 1.5 * base_rpm
        rpm = max(min_rpm, min(rpm, max_rpm))

        # Set propeller speeds
        drone.set_propellels_rpm([rpm, rpm, rpm, rpm])

        # Step physics
        scene.step()

        last_error = error

if __name__ == "__main__":
    main()
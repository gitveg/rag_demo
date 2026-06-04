import numpy as np
import genesis as gs

def main():
    gs.init(backend=gs.cpu)

    viewer_options = gs.options.ViewerOptions(
        camera_pos=(2.5, 0.0, 2.0),
        camera_lookat=(0.0, 0.0, 1.0),
        camera_fov=40,
        max_FPS=60,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        rigid_options=gs.options.RigidOptions(),
    )

    # Ground plane
    plane = scene.add_entity(
        morph=gs.morphs.Plane(),
    )

    # Drone
    drone = scene.add_entity(
        morph=gs.morphs.Drone(),
    )

    scene.build()

    # Simulation parameters
    dt = 1.0 / 60.0
    hover_height = 2.0
    takeoff_duration = 2.0   # seconds
    hover_duration = 3.0
    land_duration = 2.0

    # Motor control values (thrust, between 0 and 1)
    # We'll use a simple proportional control to maintain height
    hover_thrust = 0.65  # approximate thrust to hover
    takeoff_thrust = 0.8
    land_thrust = 0.3

    time = 0.0
    while time < takeoff_duration + hover_duration + land_duration:
        # Determine phase
        if time < takeoff_duration:
            # Takeoff: increase thrust linearly
            t = time / takeoff_duration
            thrust = takeoff_thrust * t + (1 - t) * 0.5  # start from low
        elif time < takeoff_duration + hover_duration:
            # Hover: maintain altitude with slight correction
            # Read current height
            height = drone.get_pos()[2]
            error = hover_height - height
            # Simple P control
            thrust = hover_thrust + 0.1 * error
            thrust = np.clip(thrust, 0.4, 1.0)
        else:
            # Land: decrease thrust gradually
            t = (time - takeoff_duration - hover_duration) / land_duration
            thrust = max(0.3 * (1 - t), 0.0)

        # Apply motor commands (all four motors)
        motor_values = np.full(4, thrust)
        drone.set_motors_direct(motor_values)

        scene.step()
        time += dt

    # After landing, stop all motors
    drone.set_motors_direct(np.zeros(4))
    for _ in range(100):
        scene.step()

if __name__ == "__main__":
    main()
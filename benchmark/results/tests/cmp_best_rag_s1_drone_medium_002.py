import numpy as np
import genesis as gs


def main():
    ########################## init ##########################
    gs.init(backend=gs.cpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(3.0, 2.0, 2.0),
        camera_lookat=(0.0, 0.0, 0.8),
        camera_fov=40,
        max_FPS=60,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
    )

    ########################## add entities ##########################
    # Ground plane
    scene.add_entity(
        gs.morphs.Plane(),
    )

    # Crazyflie 2.P drone
    drone = scene.add_entity(
        gs.morphs.Drone(
            file="urdf/drones/cf2p.urdf",
            model="CF2P",
        ),
    )

    ########################## build scene ##########################
    scene.build()

    # Define three floating checkpoints and a landing target
    checkpoints = [
        np.array([1.0, 0.5, 0.8]),
        np.array([0.0, 1.5, 1.2]),
        np.array([-1.0, 0.5, 0.8]),
    ]
    landing_target = np.array([0.0, 0.0, 0.05])

    # Visualize checkpoints (green) and landing target (red)
    for cp in checkpoints:
        scene.draw_debug_spheres(poss=[cp], radius=0.08, color=(0.0, 1.0, 0.0, 0.8))
    scene.draw_debug_spheres(poss=[landing_target], radius=0.12, color=(1.0, 0.0, 0.0, 0.8))

    # Hover base RPM for Crazyflie 2.P
    base_rpm = 15000.0
    max_rpm = 25000.0
    min_rpm = 0.0

    # PID gains
    Kp_xy = 3.0
    Kd_xy = 1.5
    Kp_z = 4000.0
    Kd_z = 2000.0
    Kp_att = 600.0

    phase = "takeoff"
    takeoff_height = 0.5
    wp_idx = 0
    waypoint_threshold = 0.15
    land_threshold = 0.03

    prev_pos_error = np.zeros(3)
    dt = 0.01

    print("Starting Crazyflie 2.P mission...")
    print("Phase: Takeoff")

    for step in range(3000):
        pos = drone.get_pos()

        # Determine current target based on mission phase
        if phase == "takeoff":
            target = np.array([pos[0], pos[1], takeoff_height])
            if abs(pos[2] - takeoff_height) < 0.1:
                phase = "waypoints"
                print(f"Takeoff done. Flying to waypoint {wp_idx + 1}")
        elif phase == "waypoints":
            if wp_idx < len(checkpoints):
                target = checkpoints[wp_idx]
                dist = np.linalg.norm(pos - target)
                if dist < waypoint_threshold:
                    print(f"Waypoint {wp_idx + 1} reached!")
                    wp_idx += 1
                    if wp_idx >= len(checkpoints):
                        phase = "landing"
                        print("Navigating to landing target...")
                    else:
                        print(f"Flying to waypoint {wp_idx + 1}")
            else:
                phase = "landing"
                print("Landing...")
        elif phase == "landing":
            target = landing_target
            if pos[2] < land_threshold:
                print("Landed successfully!")
                drone.set_propellels_rpm([0.0, 0.0, 0.0, 0.0])
                for _ in range(50):
                    scene.step()
                break

        # Position error and velocity approximation
        pos_error = target - pos
        vel_error = (pos_error - prev_pos_error) / dt
        prev_pos_error = pos_error.copy()

        # Compute desired pitch and roll from horizontal position error
        desired_pitch = -Kp_xy * pos_error[0] - Kd_xy * vel_error[0]
        desired_roll = Kp_xy * pos_error[1] + Kd_xy * vel_error[1]

        # Clamp desired attitude angles
        desired_pitch = np.clip(desired_pitch, -0.4, 0.4)
        desired_roll = np.clip(desired_roll, -0.4, 0.4)

        # Thrust adjustment from altitude error
        thrust_adj = Kp_z * pos_error[2] + Kd_z * vel_error[2]

        # Motor differentials for pitch and roll
        pitch_diff = desired_pitch * Kp_att
        roll_diff = desired_roll * Kp_att

        # X-configuration motor mixing: [front-left, front-right, back-right, back-left]
        rpms = [
            base_rpm + thrust_adj - pitch_diff - roll_diff,  # front-left
            base_rpm + thrust_adj - pitch_diff + roll_diff,  # front-right
            base_rpm + thrust_adj + pitch_diff + roll_diff,  # back-right
            base_rpm + thrust_adj + pitch_diff - roll_diff,  # back-left
        ]

        # Clamp motor RPMs
        rpms = [np.clip(r, min_rpm, max_rpm) for r in rpms]

        drone.set_propellels_rpm(rpms)
        scene.step()

    print("Mission complete.")


if __name__ == "__main__":
    main()
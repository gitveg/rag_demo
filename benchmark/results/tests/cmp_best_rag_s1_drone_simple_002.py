import numpy as np

import genesis as gs


def main():
    gs.init(backend=gs.cpu)

    scene = gs.Scene(
        show_viewer=True,
    )

    # Add ground plane
    plane = scene.add_entity(gs.morphs.Plane())

    # Add Crazyflie drone
    drone = scene.add_entity(
        gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            model="CF2X",
            pos=(0.0, 0.0, 0.1),  # start slightly above ground
        ),
    )

    scene.build()

    # Control parameters
    TARGET_Z = 1.5
    BASE_RPM = 14468.429183500699
    MIN_RPM = 0.9 * BASE_RPM
    MAX_RPM = 1.5 * BASE_RPM
    kp = 50.0
    kd = 10.0

    dt = 0.01  # simulation timestep
    prev_error = 0.0

    # Take-off and hover loop
    for _ in range(2000):
        pos = drone.get_pos()
        current_z = pos[2]

        error = TARGET_Z - current_z
        derivative = (error - prev_error) / dt
        rpm = BASE_RPM + kp * error + kd * derivative
        rpm = np.clip(rpm, MIN_RPM, MAX_RPM)
        prev_error = error

        drone.set_propellels_rpm([rpm] * 4)
        scene.step()


if __name__ == "__main__":
    main()
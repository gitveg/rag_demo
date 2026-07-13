import numpy as np
import genesis as gs

def main():
    gs.init()
    scene = gs.Scene(show_viewer=True)

    # Ground plane
    plane = scene.add_entity(gs.morphs.Plane())

    # Crazyflie 2.X drone
    drone = scene.add_entity(
        gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            model="CF2X",
            pos=(0.0, 0.0, 0.02),
        ),
    )

    scene.build()

    # Target altitude and gains
    target_height = 1.5
    kp = 3000.0
    kd = 1000.0
    hover_rpm = 14475.8   # approximate hover thrust

    prev_error = 0.0

    # Simulation loop
    while scene.viewer.is_alive():
        current_height = drone.get_pos()[2]
        error = target_height - current_height
        d_error = error - prev_error

        # PD control
        thrust = hover_rpm + kp * error + kd * d_error
        thrust = np.clip(thrust, 0, 30000)

        drone.set_propeller_rpms([thrust] * 4)
        prev_error = error

        scene.step()

if __name__ == "__main__":
    main()
import numpy as np
import genesis as gs


def main():
    gs.init(backend=gs.cpu)

    viewer_options = gs.options.ViewerOptions(
        camera_pos=(2.5, 0.0, 1.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
        max_FPS=60,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        show_viewer=True,
    )

    # Ground plane
    plane = scene.add_entity(
        morph=gs.options.morphs.Plane(),
    )

    # Drone
    drone = scene.add_entity(
        morph=gs.options.morphs.Drone(pos=(0.0, 0.0, 2.0)),
    )

    scene.build()

    n_dofs = drone.n_dofs
    drone.set_dofs_kp(np.full(n_dofs, 10.0))
    drone.set_dofs_kv(np.full(n_dofs, 1.0))

    # Force range for each dof (motor thrust)
    force_range = np.array([-100.0, 100.0])
    drone.set_dofs_force_range(np.tile(force_range, (n_dofs, 1)))

    # Desired altitude
    z_des = 2.0
    g = 9.81
    # Approximate mass of the drone (can be obtained from entity, but we set a reasonable value)
    # For simplicity, we assume mass = 1.0 kg (the default drone mass)
    mass = 1.0
    hover_thrust = mass * g / n_dofs  # per motor thrust to hover

    # PD gains for altitude control
    kp_z = 10.0
    kd_z = 2.0

    for i in range(2000):  # run for enough steps
        pos = drone.get_pos()
        vel = drone.get_vel()  # linear velocity
        z = pos[2]
        vz = vel[2]

        # Compute total thrust needed
        thrust_total = mass * g + kp_z * (z_des - z) - kd_z * vz
        thrust_per_motor = np.clip(thrust_total / n_dofs, -95.0, 95.0)

        # Set control forces on each motor dof
        drone.set_dofs_controls(np.full(n_dofs, thrust_per_motor))

        scene.step()


if __name__ == "__main__":
    main()
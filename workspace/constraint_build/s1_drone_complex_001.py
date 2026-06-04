import numpy as np
import genesis as gs


def main():
    gs.init(backend=gs.cpu)

    viewer_options = gs.options.ViewerOptions(
        camera_pos=(3.0, -3.0, 2.0),
        camera_lookat=(0.0, 0.0, 1.0),
        camera_fov=40,
        max_FPS=60,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        show_viewer=True,
    )

    # Ground plane
    plane = scene.add_entity(
        gs.morphs.Plane(),
    )

    # Drone
    drone = scene.add_entity(
        gs.morphs.Drone(),
    )

    # Build the scene
    scene.build()

    # Simulation parameters
    dt = 0.01  # 100 Hz
    hover_thrust = 146.0  # approximate hover thrust per motor for this drone
    forward_speed = 1.0  # m/s
    turn_rate = np.pi / 2  # rad/s

    # Time for each leg and turn
    leg_duration = 3.0 / forward_speed  # 3 s
    turn_duration = (np.pi / 2) / turn_rate  # 1 s
    leg_steps = int(leg_duration / dt)
    turn_steps = int(turn_duration / dt)

    # Motor layout indices: [m0, m1, m2, m3] (CW, CCW, CW, CCW)
    # For forward motion: increase rear motors (m1, m3)
    # For turning: increase diagonal pair (m0, m2) or (m1, m3)
    # We'll use differential thrust:
    # forward: add forward_power to rear motors, subtract from front
    # turn: add turn_power to one diagonal, subtract from the other
    # To maintain altitude, overall thrust must equal hover_thrust * 4.

    # Base motor speeds for hover
    base_speed = hover_thrust  # assume linear relationship

    def compute_motor_speeds(forward_cmd, turn_cmd):
        # forward_cmd: positive = forward
        # turn_cmd: positive = clockwise (right)
        # Mapping: m0 (front-left, CW), m1 (rear-left, CCW), m2 (front-right, CW), m3 (rear-right, CCW)
        # For forward: + on m1 and m3, - on m0 and m2
        # For yaw (right): + on m0 and m3, - on m1 and m2 (or opposite, adjust sign)
        # We assume this mapping works
        m = np.array([base_speed] * 4, dtype=float)
        m[0] += -forward_cmd + turn_cmd
        m[1] +=  forward_cmd + turn_cmd
        m[2] += -forward_cmd - turn_cmd
        m[3] +=  forward_cmd - turn_cmd
        # Ensure non-negative
        m = np.clip(m, 0, None)
        return m

    # Square path: 4 legs and 4 turns
    seq = []
    for _ in range(4):
        seq.extend([('forward', leg_steps), ('turn', turn_steps)])

    step_count = 0
    total_steps = sum(steps for _, steps in seq)
    for action, steps in seq:
        if action == 'forward':
            forward_cmd = 20.0  # arbitrary scaling
            turn_cmd = 0.0
        else:  # turn
            forward_cmd = 0.0
            turn_cmd = 10.0  # scaling for 90 deg turn

        for _ in range(steps):
            motor_speeds = compute_motor_speeds(forward_cmd, turn_cmd)
            drone.set_dofs_velocity(motor_speeds)
            scene.step()
            step_count += 1

    # Landing: reduce thrust to zero
    landing_steps = 50
    for _ in range(landing_steps):
        motor_speeds = np.array([0.0] * 4)
        drone.set_dofs_velocity(motor_speeds)
        scene.step()

    print("Drone finished square path and landed.")


if __name__ == "__main__":
    main()
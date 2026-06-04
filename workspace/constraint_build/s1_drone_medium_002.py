import argparse
import numpy as np
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(2.5, 0.0, 1.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
        max_FPS=60,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        show_viewer=args.vis,
        show_FPS=True,
    )

    ########################## add entities ##########################
    plane = scene.add_entity(gs.morphs.Plane())
    drone = scene.add_entity(gs.morphs.Drone())

    ########################## build scene ##########################
    scene.build()

    # Checkpoint positions (x, y, z) – floating points the drone must pass through
    checkpoints = [
        np.array([0.5, 0.0, 0.8]),
        np.array([0.5, 0.5, 1.0]),
        np.array([-0.3, 0.5, 0.9]),
        np.array([-0.3, -0.2, 0.7]),
    ]
    target_landing = np.array([0.0, 0.0, 0.2])

    # Draw checkpoints and target as red and green dots
    scene.draw_debug_points([c for c in checkpoints], colors=(1.0, 0.0, 0.0, 0.8))
    scene.draw_debug_points([target_landing], colors=(0.0, 1.0, 0.0, 0.8))

    ########################## simulation parameters ##########################
    sim_dt = 1.0 / 60.0
    total_steps = 600  # 10 seconds at 60 Hz
    takeoff_steps = 120         # 2 sec takeoff
    cruise_steps_per_cp = 80   # per checkpoint
    landing_steps = 100

    def phase(step):
        if step < takeoff_steps:
            return 'takeoff'
        elif step < takeoff_steps + cruise_steps_per_cp * len(checkpoints):
            return 'cruise'
        else:
            return 'land'

    def get_target_pos(step):
        if step < takeoff_steps:
            # climb straight up to first checkpoint height
            frac = step / takeoff_steps
            return np.array([0.0, 0.0, frac * checkpoints[0][2]])
        elif step < takeoff_steps + cruise_steps_per_cp * len(checkpoints):
            idx = (step - takeoff_steps) // cruise_steps_per_cp
            t = ((step - takeoff_steps) % cruise_steps_per_cp) / cruise_steps_per_cp
            if idx < len(checkpoints) - 1:
                return (1 - t) * checkpoints[idx] + t * checkpoints[idx + 1]
            else:
                # after last checkpoint, glide towards landing target
                return (1 - t) * checkpoints[-1] + t * target_landing
        else:
            # descend to target
            frac = (step - (takeoff_steps + cruise_steps_per_cp * len(checkpoints))) / landing_steps
            return (1 - frac) * target_landing + np.array([0.0, 0.0, -0.1])

    # Simple PID gain for height and horizontal position (hardcoded to avoid API guess)
    kp_z = 50.0
    kp_xy = 30.0
    kd = 10.0

    prev_error = np.zeros(3)
    for step in range(total_steps):
        # get drone current position (assumes drone.pos attribute)
        current_pos = drone.pos.copy()[:3]
        target = get_target_pos(step)

        error = target - current_pos
        derror = (error - prev_error) / sim_dt
        prev_error = error.copy()

        # compute desired acceleration (open-loop gravity compensation + PD)
        acc_des = error * np.array([kp_xy, kp_xy, kp_z]) + derror * kd + np.array([0, 0, 9.81])

        # naive mapping to motor velocities (simple thrust model)
        # all motors: base thrust from desired vertical acceleration
        base_thrust = acc_des[2]  # in m/s^2
        # pitch/roll from horizontal acceleration (rotate body to produce lateral force)
        # for simplicity, use differential thrust: increase rear motors for forward, etc.
        lateral = acc_des[:2]
        # assume drone x forward, y left
        diff_forward = lateral[0] * 0.1
        diff_left = lateral[1] * 0.1

        motor_vels = base_thrust + np.array([-diff_forward - diff_left,
                                              -diff_forward + diff_left,
                                              diff_forward + diff_left,
                                              diff_forward - diff_left])

        drone.set_motor_velocity(motor_vels.astype(np.float64))

        scene.step()

    # after loop, stop motors and let the viewer run
    drone.set_motor_velocity(np.zeros(4))
    print("Drone simulation finished. Close window to exit.")


if __name__ == "__main__":
    main()
import numpy as np
import genesis as gs
from genesis.utils.geom import quat_to_xyz


def main():
    gs.init(backend=gs.cpu)

    viewer_options = gs.options.ViewerOptions(
        camera_pos=(5.0, 0.0, 3.0),
        camera_lookat=(0.0, 0.0, 1.0),
        camera_fov=40,
        max_FPS=60,
    )
    scene = gs.Scene(viewer_options=viewer_options, show_viewer=True)

    scene.add_entity(gs.morphs.Plane())
    drone = scene.add_entity(
        gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            model="CF2X",
            pos=(0.0, 0.0, 1.0),
        )
    )

    scene.build()

    # PID gains
    Kp_xy = 5.0
    Kd_xy = 3.0
    Kp_z = 8.0
    Kd_z = 4.0

    roll_p_gain = 0.5
    pitch_p_gain = 0.5

    # Hover RPM from reference
    base_rpm = 14468.429183500699
    min_rpm = 0.9 * base_rpm
    max_rpm = 1.5 * base_rpm

    target_z = 1.0
    radius = 2.0
    omega = 0.5  # rad/s
    dt = 0.01    # assumed simulation timestep

    prev_pos = np.array([0.0, 0.0, 1.0])

    for step in range(2000):
        t = step * dt

        # Circle trajectory
        target_xy = np.array([radius * np.cos(omega * t), radius * np.sin(omega * t)])
        target_vel_xy = np.array([-radius * omega * np.sin(omega * t),
                                  radius * omega * np.cos(omega * t)])
        target_acc_xy = np.array([-radius * omega**2 * np.cos(omega * t),
                                  -radius * omega**2 * np.sin(omega * t)])

        cur_pos = np.array(drone.get_pos())
        cur_quat = np.array(drone.get_quat())
        cur_euler = quat_to_xyz(cur_quat)  # (roll, pitch, yaw)
        cur_roll, cur_pitch, cur_yaw = cur_euler

        cur_vel = (cur_pos - prev_pos) / dt

        # Position & velocity errors
        pos_err = np.array([target_xy[0], target_xy[1], target_z]) - cur_pos
        vel_err = np.concatenate([target_vel_xy, [0.0]]) - cur_vel

        # Desired horizontal accelerations (world frame)
        des_acc_xy = target_acc_xy + Kp_xy * pos_err[:2] + Kd_xy * vel_err[:2]

        # Desired roll/pitch from horizontal acceleration
        g = 9.81
        des_roll = des_acc_xy[1] / g
        des_pitch = -des_acc_xy[0] / g
        max_tilt = np.deg2rad(30)
        des_roll = np.clip(des_roll, -max_tilt, max_tilt)
        des_pitch = np.clip(des_pitch, -max_tilt, max_tilt)

        # Altitude control -> base RPM adjustment
        thrust_rpm = base_rpm + Kp_z * pos_err[2] - Kd_z * cur_vel[2]

        # Attitude errors
        roll_err = des_roll - cur_roll
        pitch_err = des_pitch - cur_pitch

        # Differential RPM for roll / pitch
        roll_diff = roll_p_gain * roll_err * base_rpm
        pitch_diff = pitch_p_gain * pitch_err * base_rpm

        # Motor mapping (X configuration: FR, FL, RL, RR)
        rpm = np.zeros(4)
        rpm[0] = thrust_rpm + roll_diff - pitch_diff  # FR
        rpm[1] = thrust_rpm - roll_diff - pitch_diff  # FL
        rpm[2] = thrust_rpm - roll_diff + pitch_diff  # RL
        rpm[3] = thrust_rpm + roll_diff + pitch_diff  # RR

        rpm = np.clip(rpm, min_rpm, max_rpm)

        drone.set_propellels_rpm(rpm.tolist())

        prev_pos = cur_pos

        scene.step()


if __name__ == "__main__":
    main()
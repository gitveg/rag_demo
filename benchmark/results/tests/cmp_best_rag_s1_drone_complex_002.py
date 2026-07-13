import argparse
import numpy as np

import genesis as gs


class DroneController:
    """A simple PID-based controller for a quadrotor drone."""

    def __init__(self, base_rpm):
        self.base_rpm = base_rpm
        # PID gains
        self.Kp_alt = 150.0   # thrust delta per meter of altitude error
        self.Kd_alt = 50.0
        self.Kp_xy = 100.0    # roll/pitch delta per meter of horizontal error
        self.Kd_xy = 30.0
        self.Kp_yaw = 80.0
        self.Kd_yaw = 30.0

        self.prev_alt_error = 0.0
        self.prev_xy_error = np.zeros(2)
        self.prev_yaw_error = 0.0

        self.min_rpm = 0.9 * base_rpm
        self.max_rpm = 1.5 * base_rpm

        # Motor layout: indices 0:front-right, 1:front-left, 2:rear-left, 3:rear-right
        self.motor_signs = {
            "pitch": [-1, -1, 1, 1],   # pos pitch -> nose down -> rear up
            "roll":  [-1, 1, 1, -1],   # pos roll -> right side up -> left up
            "yaw":   [1, -1, 1, -1],   # pos yaw -> turn right? (adjust if needed)
        }

    def _clamp(self, rpm):
        return max(self.min_rpm, min(self.max_rpm, rpm))

    def get_rpms(self, target_pos, drone_pos, drone_quat, drone_vel, drone_ang_vel, dt):
        """
        Compute motor RPMs to fly toward target_pos.
        target_pos: (x, y, z)
        drone_pos, drone_quat, drone_vel, drone_ang_vel: current state
        dt: time step
        """
        # altitude PID
        alt_error = target_pos[2] - drone_pos[2]
        d_alt = (alt_error - self.prev_alt_error) / dt if dt > 0 else 0
        thrust_adj = self.Kp_alt * alt_error + self.Kd_alt * d_alt
        self.prev_alt_error = alt_error

        # horizontal position control -> desired roll/pitch
        xy_error = target_pos[:2] - drone_pos[:2]
        d_xy = (xy_error - self.prev_xy_error) / dt if dt > 0 else np.zeros(2)
        pitch_cmd = -self.Kp_xy * xy_error[0] - self.Kd_xy * d_xy[0]   # forward is +x, pitch down -> negative
        roll_cmd  =  self.Kp_xy * xy_error[1] + self.Kd_xy * d_xy[1]   # left is +y, roll right -> positive?
        self.prev_xy_error = xy_error

        # yaw control (desired yaw: point toward target on ground)
        desired_yaw = np.arctan2(xy_error[1], xy_error[0])
        # extract current yaw from quaternion (z-up frame)
        qx, qy, qz, qw = drone_quat
        # default quat order (x,y,z,w) in Genesis
        current_yaw = np.arctan2(2.0 * (qw * qz + qx * qy),
                                 1.0 - 2.0 * (qy * qy + qz * qz))
        yaw_error = desired_yaw - current_yaw
        # wrap to [-pi, pi]
        yaw_error = (yaw_error + np.pi) % (2 * np.pi) - np.pi
        d_yaw = (yaw_error - self.prev_yaw_error) / dt if dt > 0 else 0
        yaw_cmd = self.Kp_yaw * yaw_error + self.Kd_yaw * d_yaw
        self.prev_yaw_error = yaw_error

        # combine commands into RPM
        rpms = np.full(4, self.base_rpm)
        rpms += thrust_adj
        rpms += np.array(self.motor_signs["pitch"]) * pitch_cmd
        rpms += np.array(self.motor_signs["roll"]) * roll_cmd
        rpms += np.array(self.motor_signs["yaw"]) * yaw_cmd

        # clamp and cast to int
        rpms = np.clip(rpms, self.min_rpm, self.max_rpm).astype(int)
        return rpms.tolist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    # Initialization
    gs.init(backend=gs.cpu, precision="32")

    # Scene configuration
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(5.0, -10.0, 6.0),
        camera_lookat=(5.0, 5.0, 1.0),
        camera_fov=40,
    )
    sim_dt = 0.004  # 4 ms
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=sim_dt),
        viewer_options=viewer_options,
        show_viewer=args.vis,
    )

    # Ground plane
    scene.add_entity(gs.morphs.Plane())

    # Static buildings (urban structures)
    # Tall building blockers
    building_configs = [
        {"pos": (3.0, 2.0, 1.5), "size": (0.4, 0.4, 3.0)},
        {"pos": (3.0, 4.0, 1.5), "size": (0.4, 0.4, 3.0)},
        {"pos": (3.0, 6.0, 1.5), "size": (0.4, 0.4, 3.0)},
        {"pos": (7.0, 2.0, 1.5), "size": (0.4, 0.4, 3.0)},
        {"pos": (7.0, 4.0, 1.5), "size": (0.4, 0.4, 3.0)},
        {"pos": (7.0, 6.0, 1.5), "size": (0.4, 0.4, 3.0)},
        # Low walls along the sides
        {"pos": (5.0, 0.5, 0.5), "size": (10.0, 0.2, 1.0)},
        {"pos": (5.0, 8.5, 0.5), "size": (10.0, 0.2, 1.0)},
    ]
    for cfg in building_configs:
        scene.add_entity(
            gs.morphs.Box(pos=cfg["pos"], size=cfg["size"]),
            material=gs.materials.Rigid(fixed=True),
        )

    # Moving barriers (sliding walls)
    moving_barriers = []
    barrier_data = [
        {"pos": (1.0, 4.5, 0.75), "size": (0.2, 2.0, 1.5), "axis": "x", "amplitude": 2.0, "freq": 0.8},
        {"pos": (9.0, 4.5, 0.75), "size": (0.2, 2.0, 1.5), "axis": "x", "amplitude": 2.0, "freq": 0.6},
        {"pos": (5.0, 1.5, 0.75), "size": (2.0, 0.2, 1.5), "axis": "y", "amplitude": 2.0, "freq": 0.7},
        {"pos": (5.0, 7.5, 0.75), "size": (2.0, 0.2, 1.5), "axis": "y", "amplitude": 2.0, "freq": 0.9},
    ]
    for cfg in barrier_data:
        box = scene.add_entity(
            gs.morphs.Box(pos=cfg["pos"], size=cfg["size"]),
            material=gs.materials.Rigid(fixed=False),  # dynamic, but we'll force position
        )
        moving_barriers.append((box, cfg))

    # Drone
    start_pos = (0.5, 4.5, 1.5)  # start in the middle of the hallway
    drone = scene.add_entity(gs.morphs.Drone(pos=start_pos, fixed=False))

    # Build scene
    scene.build()

    # Drone controller
    base_rpm = 14468.429183500699
    controller = DroneController(base_rpm)

    # Waypoints for autonomous navigation through the course
    waypoints = [
        np.array([0.5, 4.5, 1.5]),   # start hover
        np.array([1.5, 4.5, 1.5]),
        np.array([2.5, 4.5, 2.0]),   # climb over low moving barrier
        np.array([4.0, 4.5, 2.0]),
        np.array([5.0, 4.5, 2.0]),   # pass through gap between moving barriers
        np.array([6.0, 4.5, 2.0]),
        np.array([8.0, 4.5, 1.5]),
        np.array([9.5, 4.5, 1.5]),   # exit
        np.array([9.5, 1.5, 1.5]),   # turn right behind building
        np.array([0.5, 1.5, 1.5]),   # return along the back alley
    ]
    current_wp_idx = 0
    wp_tolerance = 0.15  # metres

    # Simulation loop
    sim_steps = 3500
    for step in range(sim_steps):
        t = step * sim_dt

        # Update moving barriers
        for box, cfg in moving_barriers:
            if cfg["axis"] == "x":
                new_x = cfg["pos"][0] + cfg["amplitude"] * np.sin(2 * np.pi * cfg["freq"] * t)
                new_pos = (new_x, cfg["pos"][1], cfg["pos"][2])
            else:  # y axis
                new_y = cfg["pos"][1] + cfg["amplitude"] * np.sin(2 * np.pi * cfg["freq"] * t)
                new_pos = (cfg["pos"][0], new_y, cfg["pos"][2])
            box.set_pos(new_pos)
            box.set_vel(np.zeros(3))
            box.set_ang_vel(np.zeros(3))

        # Get drone state
        drone_pos = drone.get_pos()
        drone_quat = drone.get_quat()
        drone_vel = drone.get_vel()
        drone_ang_vel = drone.get_ang_vel()

        # Waypoint following
        target = waypoints[current_wp_idx]
        rpms = controller.get_rpms(target, drone_pos, drone_quat, drone_vel, drone_ang_vel, sim_dt)

        # Advance to next waypoint if close enough
        dist = np.linalg.norm(target - drone_pos)
        if dist < wp_tolerance and current_wp_idx < len(waypoints) - 1:
            current_wp_idx += 1

        # Apply motor commands
        drone.set_propellels_rpm(rpms)

        # Step physics
        scene.step()

        # Optional: print status
        if step % 100 == 0:
            print(f"Step {step}, pos {drone_pos}, target {current_wp_idx} / {len(waypoints)-1}")

    print("Simulation finished.")


if __name__ == "__main__":
    main()
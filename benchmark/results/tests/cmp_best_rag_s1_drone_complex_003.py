import numpy as np
import genesis as gs
from genesis.utils.geom import quat_to_xyz

class DronePIDController:
    def __init__(self, base_rpm, min_rpm, max_rpm, dt=0.02):
        self.base_rpm = base_rpm
        self.min_rpm = min_rpm
        self.max_rpm = max_rpm
        self.dt = dt

        # Gains (manually tuned for demonstration)
        self.Kp_z = 2.5e3
        self.Kd_z = 1.2e3
        self.Kp_xy = 0.8
        self.Kd_xy = 0.4
        self.Kp_yaw = 0.6

        self.target_pos = np.array([0.0, 0.0, 1.0])
        self.target_yaw = 0.0
        self.prev_error_pos = np.zeros(3)

    def set_target(self, pos, yaw=0.0):
        self.target_pos = np.array(pos)
        self.target_yaw = yaw

    def update(self, current_pos, current_quat):
        error_pos = self.target_pos - current_pos

        # Altitude control
        z_error = error_pos[2]
        z_vel = (error_pos[2] - self.prev_error_pos[2]) / self.dt
        thrust_adjust = self.Kp_z * z_error + self.Kd_z * z_vel
        thrust = self.base_rpm + thrust_adjust

        # Horizontal control -> desired roll/pitch (small-angle world-frame approximation)
        # x forward, y left, z up
        pitch_des = -self.Kp_xy * error_pos[0]   # forward => negative pitch
        roll_des = self.Kp_xy * error_pos[1]     # right => positive roll

        # Yaw control
        r, p, current_yaw = quat_to_xyz(current_quat)
        yaw_error = self.target_yaw - current_yaw
        # wrap to [-pi, pi]
        yaw_error = (yaw_error + np.pi) % (2 * np.pi) - np.pi
        yaw_des = self.Kp_yaw * yaw_error

        # Motor mixing (X-config)
        m1 = thrust - roll_des + pitch_des - yaw_des
        m2 = thrust + roll_des + pitch_des + yaw_des
        m3 = thrust + roll_des - pitch_des - yaw_des
        m4 = thrust - roll_des - pitch_des + yaw_des

        # Clamp RPMs
        m1 = np.clip(m1, self.min_rpm, self.max_rpm)
        m2 = np.clip(m2, self.min_rpm, self.max_rpm)
        m3 = np.clip(m3, self.min_rpm, self.max_rpm)
        m4 = np.clip(m4, self.min_rpm, self.max_rpm)

        self.prev_error_pos = error_pos.copy()
        return [m1, m2, m3, m4]

def main():
    gs.init(backend=gs.cpu)

    viewer_options = gs.options.ViewerOptions(
        camera_pos=(5.0, -3.0, 2.5),
        camera_lookat=(2.5, 0.0, 1.5),
        camera_fov=50,
        max_FPS=60,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        show_viewer=True,
    )

    plane = scene.add_entity(gs.morphs.Plane())
    drone = scene.add_entity(
        gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            model="CF2X",
            pos=(0.0, 0.0, 0.2),
        )
    )

    # Positions for three upright hoops (approximated by thin vertical boxes)
    hoop_centers = [
        (1.5, 0.0, 1.0),
        (3.0, 0.0, 1.6),
        (4.5, 0.0, 2.2),
    ]
    for pos in hoop_centers:
        scene.add_entity(
            gs.morphs.Box(
                pos=pos,
                size=(0.02, 0.6, 0.6),  # thin vertical slab to indicate hoop
                fixed=True,
                # no collision needed, just visual
            )
        )

    scene.build()

    # Drone hover parameters (from reference)
    base_rpm = 14468.429183500699
    min_rpm = 0.9 * base_rpm
    max_rpm = 1.5 * base_rpm
    controller = DronePIDController(base_rpm, min_rpm, max_rpm, dt=0.02)

    # Waypoints: three hoops + landing
    waypoints = [
        hoop_centers[0],
        hoop_centers[1],
        hoop_centers[2],
        # Land at a point ahead, slightly above ground
        (5.5, 0.0, 0.15),
    ]

    # Initial hover at takeoff position
    controller.set_target(waypoints[0])
    # Takeoff: rise to first hoop height before moving
    takeoff_pos = np.array([0.0, 0.0, waypoints[0][2]])
    controller.set_target(takeoff_pos)
    print("Taking off...")
    for _ in range(200):
        pos = drone.get_pos()
        quat = drone.get_quat()
        rpms = controller.update(pos, quat)
        drone.set_propellels_rpm(rpms)
        scene.step()

    # Navigate through waypoints
    arrival_threshold = 0.15
    for i, wp in enumerate(waypoints):
        print(f"Flying to waypoint {i+1}: {wp}")
        controller.set_target(wp)
        steps = 0
        while steps < 600:  # safety limit
            pos = drone.get_pos()
            quat = drone.get_quat()
            dist = np.linalg.norm(pos - np.array(wp))
            if dist < arrival_threshold:
                break
            rpms = controller.update(pos, quat)
            drone.set_propellels_rpm(rpms)
            scene.step()
            steps += 1

    # Final landing: descend slowly and cut thrust
    print("Landing...")
    # lower altitude slowly
    land_pos = np.array([5.5, 0.0, 0.08])
    controller.set_target(land_pos)
    for _ in range(150):
        pos = drone.get_pos()
        quat = drone.get_quat()
        rpms = controller.update(pos, quat)
        drone.set_propellels_rpm(rpms)
        scene.step()

    # Shut off motors
    print("Motors off.")
    for _ in range(100):
        drone.set_propellels_rpm([0, 0, 0, 0])
        scene.step()

    print("Done.")

if __name__ == "__main__":
    main()
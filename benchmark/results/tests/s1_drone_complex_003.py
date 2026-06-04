"""
User Query: Simulate a Crazyflie 2.X drone (use gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X")) navigating through three upright hoops at different heights, then land safely.
task_id: s1_drone_complex_003
"""

import math
import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=0.01),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(6.0, -6.0, 4.0),
            camera_lookat=(2.5, 0.0, 1.2),
        ),
        renderer=gs.options.renderers.Rasterizer(),
    )

    scene.add_entity(
        gs.morphs.Plane(),
        material=gs.materials.Rigid(friction=1.0, coup_friction=0.1, coup_restitution=0.0),
        surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
    )

    hoop_xs = [1.5, 3.0, 4.5]
    hoop_zs = [1.0, 1.4, 0.8]
    hoop_radius = 0.6
    hoop_thickness = 0.05
    post_height = 2.2
    post_size = (0.06, 0.06, post_height)
    hoop_color = (1.0, 0.45, 0.1, 1.0)

    rigid_mat = gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0)
    hoop_surface = gs.surfaces.Rough(color=hoop_color)

    for x, zc in zip(hoop_xs, hoop_zs):
        left_y = -hoop_radius
        right_y = hoop_radius

        scene.add_entity(
            gs.morphs.Box(pos=(x, left_y, post_height * 0.5), size=post_size),
            material=rigid_mat,
            surface=hoop_surface,
        )
        scene.add_entity(
            gs.morphs.Box(pos=(x, right_y, post_height * 0.5), size=post_size),
            material=rigid_mat,
            surface=hoop_surface,
        )

        scene.add_entity(
            gs.morphs.Cylinder(
                pos=(x, 0.0, zc + hoop_radius),
                radius=hoop_thickness,
                height=2.0 * hoop_radius,
            ),
            material=rigid_mat,
            surface=hoop_surface,
        )
        scene.add_entity(
            gs.morphs.Cylinder(
                pos=(x, 0.0, zc - hoop_radius),
                radius=hoop_thickness,
                height=2.0 * hoop_radius,
            ),
            material=rigid_mat,
            surface=hoop_surface,
        )

    scene.add_camera(
        pos=(7.0, -7.0, 4.5),
        lookat=(2.5, 0.0, 1.1),
        res=(1280, 720),
        fov=50,
    )

    drone = scene.add_entity(
        gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            model="CF2X",
            pos=(0.0, 0.0, 0.25),
        )
    )

    scene.build()

    hover_rpm = 14468.429183500699

    waypoints = [
        (0.5, 0.0, 0.8),
        (1.5, 0.0, 1.0),
        (3.0, 0.0, 1.4),
        (4.5, 0.0, 0.8),
        (5.3, 0.0, 0.8),
        (5.3, 0.0, 0.25),
    ]

    waypoint_idx = 0

    kp_z = 4200.0
    kd_z = 1800.0

    kp_y = 900.0
    kd_y = 450.0

    kp_x = 650.0
    kd_x = 260.0

    max_thrust_cmd = 2500.0
    max_pitch_cmd = 900.0
    max_roll_cmd = 700.0

    prev_pos = drone.get_pos()

    total_steps = 2200
    for step in range(total_steps):
        pos = drone.get_pos()
        vel = (
            (pos[0] - prev_pos[0]) / 0.01,
            (pos[1] - prev_pos[1]) / 0.01,
            (pos[2] - prev_pos[2]) / 0.01,
        )
        prev_pos = pos

        if waypoint_idx < len(waypoints):
            target = waypoints[waypoint_idx]
            dx = target[0] - pos[0]
            dy = target[1] - pos[1]
            dz = target[2] - pos[2]

            dist_xy = math.sqrt(dx * dx + dy * dy)
            if dist_xy < 0.18 and abs(dz) < 0.15:
                waypoint_idx += 1
                if waypoint_idx < len(waypoints):
                    target = waypoints[waypoint_idx]
                    dx = target[0] - pos[0]
                    dy = target[1] - pos[1]
                    dz = target[2] - pos[2]
        else:
            target = waypoints[-1]
            dx = target[0] - pos[0]
            dy = target[1] - pos[1]
            dz = target[2] - pos[2]

        vx, vy, vz = vel

        thrust = kp_z * dz - kd_z * vz
        thrust = max(-2200.0, min(max_thrust_cmd, thrust))

        pitch = -(kp_x * dx - kd_x * vx)
        pitch = max(-max_pitch_cmd, min(max_pitch_cmd, pitch))

        roll = kp_y * dy - kd_y * vy
        roll = max(-max_roll_cmd, min(max_roll_cmd, roll))

        yaw = 0.0

        m1 = hover_rpm + thrust - roll - pitch - yaw
        m2 = hover_rpm + thrust - roll + pitch + yaw
        m3 = hover_rpm + thrust + roll + pitch - yaw
        m4 = hover_rpm + thrust + roll - pitch - yaw

        min_rpm = 0.0
        max_rpm = 25000.0
        rpms = [
            max(min_rpm, min(max_rpm, m1)),
            max(min_rpm, min(max_rpm, m2)),
            max(min_rpm, min(max_rpm, m3)),
            max(min_rpm, min(max_rpm, m4)),
        ]

        if waypoint_idx >= len(waypoints) and pos[2] < 0.12 and abs(vz) < 0.2:
            rpms = [0.0, 0.0, 0.0, 0.0]

        drone.set_propellels_rpm(rpms)
        scene.step()


if __name__ == "__main__":
    main()
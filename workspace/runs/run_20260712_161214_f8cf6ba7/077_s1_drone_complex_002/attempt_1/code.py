import argparse
import numpy as np
import genesis as gs

def compute_controller(drone, target_pos, dt, obstacle_positions, obstacle_radii, safety_dist=0.5, repulsion_gain=10.0):
    """
    Simple PID + repulsion controller for a quadcopter.
    Returns desired thrust and body torques.
    """
    # Drone state
    pos = drone.get_pos()
    vel = drone.get_vel()
    quat = drone.get_quat()
    # Convert quaternion to rotation matrix (use numpy if quat is [x,y,z,w])
    R = quat_to_rot(quat)  # body to world

    # Altitude PID
    kp_z, kd_z = 8.0, 4.0
    err_z = target_pos[2] - pos[2]
    err_zdot = -vel[2]     # target vz = 0
    thrust_z = kp_z * err_z + kd_z * err_zdot

    # Horizontal position PD
    kp_xy, kd_xy = 5.0, 3.0
    err_xy = target_pos[:2] - pos[:2]
    err_vxy = -vel[:2]     # target vxy = 0
    acc_des_xy = kp_xy * err_xy + kd_xy * err_vxy

    # Obstacle repulsion (potential field)
    rep_force = np.zeros(3)
    for obs_pos, obs_r in zip(obstacle_positions, obstacle_radii):
        dist_vec = pos - obs_pos  # vector from obstacle to drone
        d = np.linalg.norm(dist_vec)
        if d < safety_dist + obs_r and d > 0.01:
            direction = dist_vec / d
            magnitude = repulsion_gain * (1.0/(d - obs_r) - 1.0/(safety_dist))
            rep_force += direction * magnitude

    # Combine desired acceleration (in world frame)
    gravity = np.array([0., 0., -9.81])
    acc_des = np.array([acc_des_xy[0], acc_des_xy[1], 0.0]) + np.array([0., 0., thrust_z]) + rep_force
    force_des = drone_mass * (acc_des - gravity)  # total desired force in world

    # Rotate to body frame
    force_body = R.T @ force_des

    # Decompose into thrust (z body) and torques
    thrust = force_body[2]  # assume thrust along body -z? Drone usually upward thrust is positive z
    # Simple torque mapping for roll and pitch
    # Desired body x,y accelerations map to torques
    acc_body = R.T @ acc_des
    torque_roll = -drone_mass * arm_length * acc_body[1]   # moment from pitch?
    torque_pitch = drone_mass * arm_length * acc_body[0]
    torque_yaw = 0.0  # no yaw control

    # Convert thrust and torques to RPMs (simplified linear model)
    # thrust = k_f * (w1^2 + w2^2 + w3^2 + w4^2)
    # torque_roll = k_f * l * (w2^2 - w4^2)
    # torque_pitch = k_f * l * (w1^2 - w3^2)
    # torque_yaw = k_m * (w1^2 - w2^2 + w3^2 - w4^2)
    # Solve for squared speeds
    A = np.array([
        [1, 1, 1, 1],
        [0, motor_constant * arm_length, 0, -motor_constant * arm_length],
        [motor_constant * arm_length, 0, -motor_constant * arm_length, 0],
        [k_m, -k_m, k_m, -k_m]
    ])
    b = np.array([thrust / motor_constant, torque_roll, torque_pitch, torque_yaw])
    try:
        w_sq = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        w_sq = np.zeros(4)
    w_sq = np.clip(w_sq, 0, None)  # RPM squared must be positive
    rpms = np.sqrt(w_sq)
    rpms = np.clip(rpms, 0, max_rpm)
    return rpms


def quat_to_rot(q):
    x, y, z, w = q
    R = np.array([
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w, 2*x*z + 2*y*w],
        [2*x*y + 2*z*w, 1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w],
        [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x*x - 2*y*y]
    ])
    return R

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(5.0, 2.0, 5.0),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=40,
        max_FPS=60,
    )

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.01,
        ),
        viewer_options=viewer_options,
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    plane = scene.add_entity(
        gs.morphs.Plane(),
    )

    # Buildings as stationary boxes
    buildings = []
    building_layout = [
        ((-2.0, -1.5, 0.5), (0.8, 0.8, 1.0)),
        ((-2.0, 1.5, 0.5), (0.8, 0.8, 1.0)),
        ((0.0, -2.0, 0.5), (0.6, 0.6, 1.0)),
        ((0.0, 2.0, 0.5), (0.6, 0.6, 1.0)),
        ((2.0, -1.5, 0.5), (0.8, 0.8, 1.0)),
        ((2.0, 1.5, 0.5), (0.8, 0.8, 1.0)),
    ]
    for pos, size in building_layout:
        building = scene.add_entity(
            gs.morphs.Box(pos=pos, size=size, fixed=True)
        )
        buildings.append(building)

    # Moving barrier (box that oscillates)
    barrier = scene.add_entity(
        gs.morphs.Box(pos=(-1.0, 0.0, 0.3), size=(0.4, 0.4, 0.3), fixed=False)
    )
    barrier_init_pos = np.array((-1.0, 0.0, 0.3), dtype=np.float64)

    # Drone
    drone = scene.add_entity(
        morph=gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            pos=(0.0, 0.0, 0.5),
        ),
    )

    ########################## build ##########################
    scene.build(n_envs=0)

    # Drone parameters (approximate)
    global drone_mass, arm_length, motor_constant, k_m, max_rpm
    drone_mass = 0.5
    arm_length = 0.1
    motor_constant = 0.001  # thrust coefficient per RPM^2
    k_m = 0.0001            # torque coefficient per RPM^2
    max_rpm = 8000

    # Obstacle data for repulsion
    obstacle_positions = [np.array(pos) for pos, _ in building_layout]
    obstacle_radii = [max(size[0], size[1])/2 for _, size in building_layout]  # approximate

    # Waypoints to navigate through buildings
    waypoints = [
        np.array((0.0, 0.0, 1.0)),
        np.array((-1.5, -1.5, 1.0)),
        np.array((-1.5, 1.5, 1.0)),
        np.array((0.0, 0.0, 1.0)),
        np.array((1.5, -1.5, 1.0)),
        np.array((1.5, 1.5, 1.0)),
        np.array((0.0, 0.0, 1.0)),
    ]
    waypoint_idx = 0
    waypoint_tolerance = 0.2

    # Simulation loop
    sim_time = 0.0
    while sim_time < 30.0:
        # Move the barrier sinusoidally
        t = sim_time
        barrier_x = barrier_init_pos[0] + 0.5 * np.sin(2 * np.pi * 0.5 * t)
        barrier_pos = np.array([barrier_x, barrier_init_pos[1], barrier_init_pos[2]])
        barrier.set_pos(barrier_pos)

        # Get drone state
        drone_pos = drone.get_pos()

        # Switch waypoint if reached
        target = waypoints[waypoint_idx]
        dist_to_target = np.linalg.norm(drone_pos - target)
        if dist_to_target < waypoint_tolerance:
            waypoint_idx = (waypoint_idx + 1) % len(waypoints)
            target = waypoints[waypoint_idx]

        # Compute control
        rpms = compute_controller(drone, target, 0.01,
                                  obstacle_positions, obstacle_radii,
                                  safety_dist=0.5, repulsion_gain=5.0)
        drone.set_propeller_rpms(rpms)

        scene.step()
        sim_time += 0.01

if __name__ == "__main__":
    main()
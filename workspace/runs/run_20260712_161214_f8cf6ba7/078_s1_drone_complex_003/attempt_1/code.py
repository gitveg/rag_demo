import torch
import genesis as gs

def quat_from_rotation_matrix(R):
    m00, m01, m02 = R[0,0], R[0,1], R[0,2]
    m10, m11, m12 = R[1,0], R[1,1], R[1,2]
    m20, m21, m22 = R[2,0], R[2,1], R[2,2]
    trace = m00 + m11 + m22
    if trace > 0:
        s = 0.5 / torch.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (m21 - m12) * s
        y = (m02 - m20) * s
        z = (m10 - m01) * s
    elif m00 > m11 and m00 > m22:
        s = 2.0 * torch.sqrt(1.0 + m00 - m11 - m22)
        w = (m21 - m12) / s
        x = 0.25 * s
        y = (m01 + m10) / s
        z = (m02 + m20) / s
    elif m11 > m22:
        s = 2.0 * torch.sqrt(1.0 + m11 - m00 - m22)
        w = (m02 - m20) / s
        x = (m01 + m10) / s
        y = 0.25 * s
        z = (m12 + m21) / s
    else:
        s = 2.0 * torch.sqrt(1.0 + m22 - m00 - m11)
        w = (m10 - m01) / s
        x = (m02 + m20) / s
        y = (m12 + m21) / s
        z = 0.25 * s
    return torch.tensor([w, x, y, z], device=R.device)

def create_hoop(scene, cx, cy, cz, opening_width=0.8, opening_height=0.8, thickness=0.05):
    frame_width = opening_width + 2*thickness
    frame_height = opening_height + 2*thickness
    mat = gs.materials.Rigid(friction=0.5)
    # top bar
    scene.add_entity(
        morph=gs.morphs.Box(size=(thickness, frame_width, thickness), pos=(cx, cy, cz + opening_height/2 + thickness/2)),
        material=mat, fixed=True)
    # bottom bar
    scene.add_entity(
        morph=gs.morphs.Box(size=(thickness, frame_width, thickness), pos=(cx, cy, cz - opening_height/2 - thickness/2)),
        material=mat, fixed=True)
    # left bar
    scene.add_entity(
        morph=gs.morphs.Box(size=(thickness, thickness, frame_height), pos=(cx, cy - opening_width/2 - thickness/2, cz)),
        material=mat, fixed=True)
    # right bar
    scene.add_entity(
        morph=gs.morphs.Box(size=(thickness, thickness, frame_height), pos=(cx, cy + opening_width/2 + thickness/2, cz)),
        material=mat, fixed=True)

def compute_motor_forces(drone, pos_des):
    pos = drone.get_pos()
    vel = drone.get_vel()
    quat = drone.get_quat()
    omega = drone.get_ang()   # angular velocity in world frame

    m = 0.03           # Crazyflie mass ~30g
    g = 9.81
    g_vec = torch.tensor([0., 0., -g], device=pos.device)

    Kp_pos = 2.0
    Kd_pos = 1.0
    a_des = Kp_pos * (pos_des - pos) - Kd_pos * vel
    F_des = m * (a_des + g_vec)

    # desired body z direction (world frame)
    norm = torch.norm(F_des)
    if norm < 1e-3:
        body_z_w = torch.tensor([0., 0., 1.], device=pos.device)
    else:
        body_z_w = F_des / norm

    # desired yaw = 0 -> body x should be world x projected onto horizontal plane
    world_x = torch.tensor([1., 0., 0.], device=pos.device)
    dot = torch.dot(body_z_w, world_x)
    body_x_des = world_x - dot * body_z_w
    if torch.norm(body_x_des) < 1e-6:
        body_x_des = torch.tensor([0., 1., 0.], device=pos.device)
    else:
        body_x_des = body_x_des / torch.norm(body_x_des)
    body_y_des = torch.cross(body_z_w, body_x_des)

    R = torch.stack([body_x_des, body_y_des, body_z_w], dim=1)  # 3x3
    q_des = quat_from_rotation_matrix(R)

    # orientation error
    q_inv = gs.utils.geom.inv_quat(quat)
    q_err = gs.utils.geom.quat_mul(q_inv, q_des)

    theta = 2.0 * torch.acos(torch.clamp(q_err[0], -1.0, 1.0))
    sin_half = torch.sin(theta/2)
    if sin_half > 1e-6:
        axis = q_err[1:4] / sin_half
    else:
        axis = torch.zeros(3, device=q_err.device)
    e_rot = theta * axis

    Kp_rot = 5.0
    Kd_rot = 2.0
    torque_world = Kp_rot * e_rot - Kd_rot * omega

    # transform torque to body frame
    torque_body = gs.utils.geom.transform_by_quat(q_inv, torque_world)

    # total thrust
    F_total = norm
    F_total = torch.clamp(F_total, 0.0, 2.0)

    # mixing coefficients (approximate for X configuration)
    coeff_roll = 0.2
    coeff_pitch = 0.2
    coeff_yaw = 0.05

    f1 = F_total/4 + coeff_roll * torque_body[0] + coeff_pitch * torque_body[1] - coeff_yaw * torque_body[2]
    f2 = F_total/4 - coeff_roll * torque_body[0] + coeff_pitch * torque_body[1] + coeff_yaw * torque_body[2]
    f3 = F_total/4 - coeff_roll * torque_body[0] - coeff_pitch * torque_body[1] - coeff_yaw * torque_body[2]
    f4 = F_total/4 + coeff_roll * torque_body[0] - coeff_pitch * torque_body[1] + coeff_yaw * torque_body[2]

    forces = torch.stack([f1, f2, f3, f4])
    forces = torch.clamp(forces, 0.0, 0.5)
    return forces

def main():
    gs.init(backend=gs.cpu)

    sim_options = gs.options.SimOptions(dt=0.01)
    scene = gs.Scene(sim_options=sim_options,
                     show_viewer=True,
                     renderer=gs.renderers.Rasterizer())

    # ground plane
    scene.add_entity(morph=gs.morphs.Plane())

    # Crazyflie drone
    drone = scene.add_entity(
        morph=gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X", pos=(0, 0, 0.2))
    )

    # three upright hoops at different heights
    hoop_centers = [(2.0, 0.0, 1.5), (4.0, 0.0, 2.0), (6.0, 0.0, 2.5)]
    for cx, cy, cz in hoop_centers:
        create_hoop(scene, cx, cy, cz)

    scene.build(n_envs=1)

    # camera position for good view
    scene.viewer.set_camera_pose(lookat=torch.tensor([3.0, 0.0, 1.5]),
                                 pos=torch.tensor([0.0, -5.0, 3.0]))

    # waypoints for navigation
    waypoints = [
        torch.tensor([0.0, 0.0, 0.2]),   # start hover
        torch.tensor([1.0, 0.0, 1.5]),   # approach first hoop
        torch.tensor([2.0, 0.0, 1.5]),   # through first hoop
        torch.tensor([3.0, 0.0, 1.5]),   # past first hoop
        torch.tensor([3.5, 0.0, 2.0]),   # approach second hoop
        torch.tensor([4.0, 0.0, 2.0]),   # through second hoop
        torch.tensor([5.0, 0.0, 2.0]),   # past second hoop
        torch.tensor([5.5, 0.0, 2.5]),   # approach third hoop
        torch.tensor([6.0, 0.0, 2.5]),   # through third hoop
        torch.tensor([7.0, 0.0, 2.5]),   # past third hoop
        torch.tensor([8.0, 0.0, 1.0]),   # descend
        torch.tensor([8.0, 0.0, 0.2]),   # land
    ]

    scene.start_recording()
    max_steps = 1500
    wp_idx = 0

    for step in range(max_steps):
        # advance to next waypoint when close enough
        if wp_idx < len(waypoints) - 1:
            dist = torch.norm(drone.get_pos() - waypoints[wp_idx])
            if dist < 0.1:
                wp_idx += 1

        pos_des = waypoints[wp_idx]
        forces = compute_motor_forces(drone, pos_des)
        drone.set_propellels(forces.numpy())   # some versions may expect tensor
        scene.step()

    scene.viewer.save_video("drone_hoops.mp4")

if __name__ == "__main__":
    main()
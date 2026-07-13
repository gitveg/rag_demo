import genesis as gs
import numpy as np
import math

def rot_matrix_to_quat(R):
    """
    Convert a 3x3 rotation matrix to a quaternion [x, y, z, w].
    Handles degenerate cases.
    """
    assert R.shape == (3, 3)
    m00, m01, m02 = R[0]
    m10, m11, m12 = R[1]
    m20, m21, m22 = R[2]
    
    trace = m00 + m11 + m22
    
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        qw = 0.25 * s
        qx = (m21 - m12) / s
        qy = (m02 - m20) / s
        qz = (m10 - m01) / s
    elif (m00 > m11) and (m00 > m22):
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        qw = (m21 - m12) / s
        qx = 0.25 * s
        qy = (m01 + m10) / s
        qz = (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        qw = (m02 - m20) / s
        qx = (m01 + m10) / s
        qy = 0.25 * s
        qz = (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        qw = (m10 - m01) / s
        qx = (m02 + m20) / s
        qy = (m12 + m21) / s
        qz = 0.25 * s
    
    # normalize
    norm = math.sqrt(qx*qx + qy*qy + qz*qz + qw*qw)
    return np.array([qx, qy, qz, qw]) / norm


def main():
    gs.init()
    scene = gs.Scene(show_viewer=True)
    
    # Add ground plane
    plane = scene.add_entity(gs.morphs.Plane())
    
    # Add Crazyflie 2.P drone
    drone = scene.add_entity(
        gs.morphs.Drone(
            file="urdf/drones/cf2p.urdf",
            pos=(0.0, 0.0, 0.2),
            model="CF2P",
        )
    )
    
    scene.build()
    
    # Define waypoints: start (already at), three checkpoints, landing target
    waypoints = [
        np.array([0.0, 0.0, 0.2]),   # start
        np.array([2.0, 0.0, 1.0]),   # checkpoint 1
        np.array([0.0, 2.0, 1.5]),   # checkpoint 2
        np.array([-2.0, 0.0, 2.0]),  # checkpoint 3
        np.array([0.0, 0.0, 0.1]),   # landing target
    ]
    
    # Approximate segment durations in seconds
    segment_durations = [2.0, 3.0, 3.0, 4.0]
    dt = 0.01  # simulation time step
    total_steps = int(sum(segment_durations) / dt)
    
    # Build interpolated path with orientation
    path_positions = []
    path_quats = []
    
    for i in range(len(waypoints) - 1):
        p0 = waypoints[i]
        p1 = waypoints[i + 1]
        duration = segment_durations[i]
        n_steps = int(duration / dt)
        
        # Use a simple heading: drone's body x-axis points forward, z-axis up
        forward = p1 - p0
        norm_f = np.linalg.norm(forward)
        if norm_f > 1e-6:
            forward = forward / norm_f
        else:
            forward = np.array([1.0, 0.0, 0.0])
        
        # Compute rotation matrix to align body x with forward, body z with world up
        up_world = np.array([0.0, 0.0, 1.0])
        right = np.cross(up_world, forward)
        right_norm = np.linalg.norm(right)
        if right_norm > 1e-6:
            right = right / right_norm
        else:
            # forward is collinear with up, fallback right
            right = np.array([1.0, 0.0, 0.0])
        up_corrected = np.cross(forward, right)
        
        R = np.column_stack((forward, right, up_corrected))
        quat = rot_matrix_to_quat(R)
        
        for t in np.linspace(0.0, 1.0, n_steps):
            pos = p0 * (1.0 - t) + p1 * t
            path_positions.append(pos)
            path_quats.append(quat)
    
    # Run simulation along the path
    for step_idx in range(min(total_steps, len(path_positions))):
        drone.set_pos(path_positions[step_idx])
        drone.set_quat(path_quats[step_idx])
        scene.step()
    
    # Keep viewer open a bit after landing
    for _ in range(200):
        scene.step()
    
    gs.exit()

if __name__ == "__main__":
    main()
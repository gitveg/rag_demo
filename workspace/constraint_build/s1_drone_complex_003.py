import numpy as np

import genesis as gs

def main():
    ########################## init ##########################
    gs.init(backend=gs.cpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(5.0, 0.0, 3.0),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
        max_FPS=60,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        show_viewer=True,
        show_FPS=True,
    )

    ########################## add entities ##########################
    # ground plane
    plane = gs.morphs.Plane()
    scene.add_entity(plane)

    # drone
    drone = gs.morphs.Drone(
        pos=(0.0, 0.0, 0.2),
    )
    drone_entity = scene.add_entity(drone)

    ########################## build scene ##########################
    scene.build()

    ########################## define hoop waypoints ##########################
    # three hoops at different heights and positions (x, y, z)
    hoop_positions = [
        (2.0, 0.0, 1.0),
        (4.0, 1.0, 1.5),
        (6.0, -0.5, 0.8),
    ]

    # draw debug frames at hoop locations for visualization
    for pos in hoop_positions:
        T = np.eye(4)
        T[:3, 3] = pos
        scene.draw_debug_frame(T, axis_length=0.3)

    ########################## control parameters ##########################
    total_duration = 10.0  # seconds
    steps_per_second = 60
    total_steps = int(total_duration * steps_per_second)
    dt = 1.0 / steps_per_second

    # generate a simple trajectory: linear interpolation between waypoints
    # start at current position (0,0,0.2), then through hoops, then end
    waypoints = [(0.0, 0.0, 0.2)] + hoop_positions + [(8.0, 0.0, 0.5)]
    num_segments = len(waypoints) - 1
    times = np.linspace(0, total_duration, num_segments + 1)
    positions = np.array(waypoints)

    # This is a simplified control: we'll set motor velocities to approximate following the path.
    # For a real quadcopter you'd need a controller; here we just set some raw motor commands.
    # We'll compute desired roll/pitch/yaw/thrust based on current position error.
    # For simplicity, we'll just apply a constant hover thrust and small periodic adjustments.
    # But to actually pass through hoops, we'll compute target velocities.

    ########################## simulation loop ##########################
    for step in range(total_steps):
        t = step / steps_per_second

        # interpolate current target position
        for i in range(num_segments):
            if times[i] <= t <= times[i+1]:
                frac = (t - times[i]) / (times[i+1] - times[i])
                target = positions[i] + frac * (positions[i+1] - positions[i])
                break
        else:
            target = positions[-1]

        # simple controller: compute error and set motor velocities
        current_pos = drone_entity.get_pos()
        error = np.array(target) - np.array(current_pos)

        # map error to motor velocities (heuristic)
        # Motors: 0:front-right, 1:front-left, 2:rear-left, 3:rear-right
        # Hover speed ~800 rpm, adjust based on error
        hover = 800.0
        thrust_factor = 50.0
        roll_factor = 5.0
        pitch_factor = 5.0
        yaw_factor = 0.0

        # desired motor velocities
        motor_cmds = np.array([
            hover + thrust_factor * error[2] + roll_factor * error[1] + pitch_factor * error[0],
            hover + thrust_factor * error[2] - roll_factor * error[1] + pitch_factor * error[0],
            hover + thrust_factor * error[2] - roll_factor * error[1] - pitch_factor * error[0],
            hover + thrust_factor * error[2] + roll_factor * error[1] - pitch_factor * error[0],
        ])
        motor_cmds = np.clip(motor_cmds, 0, 2000)

        drone_entity.set_dofs_controls(motor_cmds)

        scene.step()

if __name__ == "__main__":
    main()
import numpy as np
import genesis as gs

def main():
    gs.init(backend=gs.cpu)

    viewer_options = gs.options.ViewerOptions(
        camera_pos=(5, 0, 2),
        camera_lookat=(0, 0, 0.5),
        camera_fov=40,
        max_FPS=60,
    )

    scene = gs.Scene(
        show_viewer=True,
        viewer_options=viewer_options,
    )

    plane = scene.add_entity(gs.morphs.Plane())
    drone = scene.add_entity(
        gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            model="CF2X",
            pos=(0, 0, 0.5),
        )
    )

    scene.build()

    # Control parameters
    hover_rpm = 14475.8
    forward_delta = 200.0
    yaw_delta = 150.0

    # Time settings (assuming dt = 0.01)
    dt = 0.01
    takeoff_steps = int(1.0 / dt)
    forward_steps = int(3.0 / dt)
    yaw_steps = int(1.0 / dt)  # to turn ~90 deg

    # Takeoff: ramp to hover
    for i in range(takeoff_steps):
        factor = (i + 1) / takeoff_steps
        rpms = [hover_rpm * factor] * 4
        drone.set_propellers_rpm(rpms)
        scene.step()

    # Four sides
    for side in range(4):
        # Move forward
        for i in range(forward_steps):
            rpms = [
                hover_rpm - forward_delta,  # front right
                hover_rpm - forward_delta,  # front left
                hover_rpm + forward_delta,  # back left
                hover_rpm + forward_delta,  # back right
            ]
            drone.set_propellers_rpm(rpms)
            scene.step()

        # Brief hover between maneuvers
        for i in range(int(0.2 / dt)):
            drone.set_propellers_rpm([hover_rpm] * 4)
            scene.step()

        # Turn right (yaw)
        for i in range(yaw_steps):
            rpms = [
                hover_rpm + yaw_delta,  # front right (CW)
                hover_rpm - yaw_delta,  # front left (CCW)
                hover_rpm + yaw_delta,  # back left (CW)
                hover_rpm - yaw_delta,  # back right (CCW)
            ]
            drone.set_propellers_rpm(rpms)
            scene.step()

        # Brief hover after yaw
        for i in range(int(0.2 / dt)):
            drone.set_propellers_rpm([hover_rpm] * 4)
            scene.step()

    # Land: ramp down
    for i in range(takeoff_steps):
        factor = 1.0 - (i + 1) / takeoff_steps
        rpms = [hover_rpm * factor] * 4
        drone.set_propellers_rpm(rpms)
        scene.step()

    # Idle on ground
    for i in range(100):
        drone.set_propellers_rpm([0.0] * 4)
        scene.step()

if __name__ == "__main__":
    main()
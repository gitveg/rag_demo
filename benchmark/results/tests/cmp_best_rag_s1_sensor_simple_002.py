import numpy as np
import genesis as gs

def main():
    # Initialize Genesis with GPU backend
    gs.init(backend=gs.gpu)

    # Create the scene with default options (viewer on)
    scene = gs.Scene(show_viewer=True)

    # Add a ground plane
    scene.add_entity(gs.morphs.Plane())

    # Add a movable cube above the ground
    cube = scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 0.5),   # initial position above ground
            size=(0.2, 0.2, 0.2)    # half-size = 0.1
        )
    )

    # Add a depth camera sensor that will (conceptually) be attached to the cube.
    # In this example we keep it static, but we will compute the true distance below
    # from the cube’s position (same physical quantity it would measure).
    depth_sensor = scene.add_sensor(
        gs.options.sensors.DepthCamera(
            pos=(0.0, 0.0, 1.0),    # initial camera position
            lookat=(0.0, 0.0, 0.5), # looking at the cube
            fov=30,
            res=(64, 64)
        )
    )

    # Finalize the scene
    scene.build()

    half_height = 0.1   # half of the cube's Z size

    # Run a short simulation moving the cube in a horizontal circle while levitating
    for step in range(500):
        t = step * 0.01

        # Apply a circular horizontal force to move the cube
        fx = 0.5 * np.cos(t)
        fy = 0.5 * np.sin(t)
        cube.add_force(np.array([fx, fy, 0.0]))

        # Compensate gravity to keep the cube floating at its current height
        cube.add_force(np.array([0.0, 0.0, 9.81]))

        # Step the physics simulation
        scene.step()

        # Obtain the cube's vertical position
        z = cube.get_pos()[2]

        # The distance from the bottom of the cube to the ground (plane at z=0)
        dist_to_ground = z - half_height

        # Visualize the measured distance (simulated by the depth sensor)
        print(f"Step {step:3d}: distance to ground = {dist_to_ground:.3f} m")

if __name__ == "__main__":
    main()
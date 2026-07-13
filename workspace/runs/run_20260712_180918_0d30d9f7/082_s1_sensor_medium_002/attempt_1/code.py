import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
            gravity=(0.0, 0.0, -10.0),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(8.0, 0.0, 5.0),
            camera_lookat=(3.0, 0.0, 0.0),
        ),
        show_viewer=True,
    )

    # Ground plane
    plane = scene.add_entity(gs.morphs.Plane())

    # Obstacles: static boxes
    obstacles = [
        ((2.0, 0.0, 0.5), (0.5, 2.0, 1.0)),
        ((4.0, -0.5, 0.5), (0.5, 1.0, 1.0)),
        ((6.0, 0.5, 0.5), (0.5, 1.0, 1.0)),
    ]
    for pos, size in obstacles:
        scene.add_entity(gs.morphs.Box(pos=pos, size=size, fixed=True))

    # Mobile robot: simple box as the body
    robot = scene.add_entity(gs.morphs.Box(pos=(0.0, 0.0, 0.2), size=(0.5, 0.3, 0.2)))

    # Lidar sensor on top of the robot
    lidar = scene.add_sensor(
        gs.sensors.Lidar(
            pos=(0.0, 0.0, 0.5),  # local offset from robot
            entity=robot,          # attach to robot
        )
    )

    scene.build()

    # Give the robot a constant forward velocity
    robot.rigid.set_vel([0.3, 0.0, 0.0])

    # Simulation loop
    for i in range(500):
        scene.step()

        # Read lidar data every 20 steps
        if i % 20 == 0:
            data = lidar.get_data()
            print(f"Step {i}: lidar distances shape: {data.shape}, first 5: {data.flatten()[:5]}")

if __name__ == "__main__":
    main()
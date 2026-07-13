import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        show_viewer=True,
        vis_options=gs.options.VisOptions(rendered_envs_idx=(0,)),
    )

    # ground plane
    scene.add_entity(gs.morphs.Plane())

    # moving cube
    cube = scene.add_entity(
        gs.morphs.Box(
            size=(0.1, 0.1, 0.1),
            pos=(0.0, -0.9, 1.0),
            euler=(15.0, 30.0, 60.0),
        )
    )

    # depth sensor attached to the cube, pointing downwards
    depth_sensor = scene.add_sensor(
        gs.sensors.DepthCamera(
            pattern=gs.sensors.DepthCameraPattern(),
            pos=(0.0, -0.9, 0.8),   # slightly below cube center
            lookat=(0.0, -0.9, -10.0),  # look straight down
            fov=60,
            res=(100, 100),
        )
    )
    depth_sensor.follow_entity(cube)

    scene.build()

    # give the cube linear and angular velocity
    cube.set_dofs_velocity([0.0, 5.0, 0.0, 0.0, 0.0, 1.0])

    for step_idx in range(100):
        scene.step()

        # visualize the measured distance (center depth)
        if step_idx % 10 == 0:
            # depth_sensor.data is expected to be a numpy array of depths
            depth_data = depth_sensor.data
            if depth_data is not None:
                center_depth = depth_data[50, 50]
                print(f"Step {step_idx}: distance to ground = {center_depth:.3f} m")
            else:
                print("Depth data not available yet.")

if __name__ == "__main__":
    main()
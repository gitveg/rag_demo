import genesis as gs


def main():
    gs.init()

    # Create scene with viewer enabled for recording
    scene = gs.Scene(
        show_viewer=True,
        sim_options=gs.options.SimOptions(
            dt=1.0 / 60.0,  # 60 fps physics
        ),
        viewer_options=gs.options.ViewerOptions(
            # Viewer should be able to record; we'll use start_recording()
        ),
        vis_options=gs.options.VisOptions(
            rendered_envs_idx=(0,),
        ),
        profiling_options=gs.options.ProfilingOptions(
            show_FPS=False,
        ),
    )

    # Add a ground plane
    scene.add_entity(morph=gs.morphs.Plane())

    # Add a soft deformable sphere (central object)
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.5, 0.5, 0.5),
            size=0.15,
        ),
        material=gs.materials.FEM.Elastic(),
    )

    # Build scene
    scene.build()

    # Add a camera for cinematic orbiting
    center = (0.5, 0.5, 0.5)
    radius = 2.5
    camera = scene.add_camera(
        pos=(radius, 0.0, 1.5),
        lookat=center,
        fov=30,
    )

    # Start recording frames
    scene.start_recording()

    # Simulate for 5 seconds at 60 fps = 300 steps
    total_steps = 300
    for step in range(total_steps):
        # Compute orbital angle (one full rotation)
        angle = 2.0 * 3.14159265 * step / total_steps
        x = center[0] + radius * gs.np.cos(angle)
        y = center[1] + radius * gs.np.sin(angle)
        z = center[2] + 0.5  # slight height variation

        # Update camera position and lookat
        camera.set_pose(pos=(x, y, z), lookat=center)

        # Advance simulation and render frame
        scene.step(update_visualizer=True, refresh_visualizer=True)

    # Save recorded video
    scene.viewer.save_video(filename="orbital_deformation.mp4")


if __name__ == "__main__":
    main()
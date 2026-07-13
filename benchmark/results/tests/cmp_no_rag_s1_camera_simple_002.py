import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        renderer=gs.renderers.Rasterizer(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, 1, 1),
            camera_lookat=(0, 0, 0.2),
        ),
    )

    # Ground plane
    plane = scene.add_entity(gs.morphs.Plane())

    # Rigid ball
    ball = scene.add_entity(
        gs.morphs.Sphere(pos=(0, 0, 1.0), radius=0.2),
        material=gs.materials.Rigid(),
    )

    scene.build()

    # Add a fixed side-view camera
    cam = scene.add_camera(
        res=(640, 480),
        pos=(3.0, 0.0, 1.0),   # side (x-axis offset)
        lookat=(0, 0, 0.5),
        fov=30,
    )

    # Record frames
    frames = []
    for _ in range(200):
        scene.step()
        cam.render()
        frames.append(cam.rgb)  # numpy array (H, W, 3)

    # Save video
    gs.utils.write_video(frames, "ball_fall.mp4", fps=30)
    print("Video saved as ball_fall.mp4")

if __name__ == "__main__":
    main()
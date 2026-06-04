import genesis as gs

def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -3.5, 2.5),
            camera_lookat=(0.0, 0.0, 1.0),
            camera_fov=40,
            max_FPS=60,
        ),
        show_viewer=True,
    )

    # Ground plane
    plane = scene.add_entity(
        morph=gs.options.morphs.Plane(),
    )

    # Static rigid box obstacle
    box = scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(1.0, 0.0, 0.5),  # above ground
            size=(0.5, 0.5, 0.5),
        ),
        material=gs.materials.Rigid(),
    )

    scene.build()

    for _ in range(200):
        scene.step()

if __name__ == "__main__":
    main()
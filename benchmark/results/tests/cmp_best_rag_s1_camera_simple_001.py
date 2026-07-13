import genesis as gs

def main():
    gs.init()
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.0, 0.0, 8.0),
            camera_lookat=(0.0, 0.0, 0.0),
            camera_fov=50,
        ),
        show_viewer=True,
    )

    # ground plane
    scene.add_entity(gs.options.morphs.Plane())
    # falling sphere
    scene.add_entity(
        gs.options.morphs.Sphere(pos=(0.0, 0.0, 3.0), radius=0.5),
    )

    scene.build()

    # let the simulation run for a while
    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()
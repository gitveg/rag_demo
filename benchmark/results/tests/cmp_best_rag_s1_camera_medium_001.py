import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, 0.0, 2.0),       # 45-degree elevation, looking at sphere
            camera_lookat=(0.0, 0.0, 1.0),
        ),
        show_viewer=True,
    )

    # Static ground plane
    scene.add_entity(gs.morphs.Plane())

    # Red falling sphere
    scene.add_entity(
        gs.morphs.Sphere(pos=(0.0, 0.0, 1.0), radius=0.1),
        surface=gs.options.surfaces.Rough(color=(1.0, 0.0, 0.0, 1.0)),
    )

    scene.build()

    # Record the simulation
    scene.start_recording()

    # Run simulation for a few seconds
    for _ in range(1000):
        scene.step()

    scene.stop_recording()

if __name__ == "__main__":
    main()
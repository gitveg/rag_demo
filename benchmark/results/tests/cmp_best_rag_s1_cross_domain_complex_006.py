import argparse
import numpy as np
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(5.0, -5.0, 3.0),
        camera_lookat=(0.0, 0.0, 1.5),
        camera_fov=40,
        max_FPS=60,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # Sandy desert terrain
    scene.add_entity(gs.options.morphs.Plane())

    # Drone starting at height
    drone = scene.add_entity(
        gs.options.morphs.Drone(pos=(0.0, 0.0, 3.0))
    )

    ########################## wind force field ##########################
    # Strong wind that will push the drone off course when it enters the cylindrical region
    wind = gs.force_fields.Wind(
        direction=(1.0, 0.3, 0.0),
        strength=25.0,
        radius=2.5,
        center=(2.0, 0.0, 3.0),
    )
    scene.add_force_field(wind)

    ########################## build and simulate ##########################
    scene.build()

    for step in range(2000):
        scene.step()


if __name__ == "__main__":
    main()
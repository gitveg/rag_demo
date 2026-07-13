import torch
import time

import genesis as gs


def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(
            gravity=(0, 0, -9.81),
        ),
        viewer_options=gs.options.ViewerOptions(
            res=(1280, 720),
            camera_pos=(0.0, 0.0, 10.0),  # top-down view
            camera_lookat=(0.0, 0.0, 0.0),
            camera_fov=50,
        ),
        show_viewer=True,
    )

    # ground plane
    plane = scene.add_entity(gs.morphs.Plane())

    # falling sphere
    sphere = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.0, 0.0, 5.0),
            radius=0.3,
        ),
    )

    scene.build()

    # simulation loop
    for _ in range(1000):
        scene.step()
        time.sleep(0.01)


if __name__ == "__main__":
    main()
import argparse
import os

import genesis as gs
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        show_viewer=args.vis,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, -1.0, 1.5),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
    )

    ########################## entities ##########################
    # slope (tilted plane)
    plane = scene.add_entity(
        morph=gs.options.morphs.Plane(
            pos=(0.0, 0.0, 0.0),
            euler=(10.0, 0.0, 0.0),  # tilt around X to make slope
        ),
        material=gs.materials.Rigid(
            friction=0.5,
        ),
    )

    # rigid box
    box = scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(0.0, 0.5, 0.0),
            size=(0.2, 0.2, 0.2),
            euler=(0.0, 0.0, 0.0),
        ),
        material=gs.materials.Rigid(
            rho=200.0,
            friction=0.3,
        ),
    )

    ########################## build ##########################
    scene.build()

    ########################## cameras ##########################
    # side camera
    cam_side = gs.Camera(
        scene,
        pos=(4.0, -3.0, 1.0),
        lookat=(0.0, 0.0, 0.5),
        fov=40,
        width=960,
        height=540,
    )
    cam_side.start_recording(
        save_path=os.path.join(os.getcwd(), "side_view.mp4"),
        fps=60,
    )

    # top camera
    cam_top = gs.Camera(
        scene,
        pos=(0.0, 0.0, 4.0),
        lookat=(0.0, 0.0, 0.0),
        fov=40,
        width=960,
        height=540,
    )
    cam_top.start_recording(
        save_path=os.path.join(os.getcwd(), "top_view.mp4"),
        fps=60,
    )

    ########################## simulate ##########################
    for i in range(1000):
        scene.step()

        # track box position for both cameras
        box_pos = box.get_pos()
        cam_side.set_lookat(box_pos)
        cam_side.set_pos(box_pos + np.array([3.0, -2.0, 0.5]))

        cam_top.set_lookat(box_pos)
        cam_top.set_pos(box_pos + np.array([0.0, 0.0, 3.5]))

    ########################## stop recording ##########################
    cam_side.stop_recording()
    cam_top.stop_recording()

    if args.vis:
        # keep viewer open after simulation
        while True:
            scene.step()


if __name__ == "__main__":
    main()
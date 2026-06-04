import argparse
import numpy as np
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(gravity=(0.0, 0.0, 0.0)),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -3.5, 2.5),
            camera_lookat=(0.0, 0.0, 1.0),
            camera_fov=40,
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    box1 = scene.add_entity(
        morph=gs.options.morphs.Box(
            size=(0.2, 0.2, 0.2),
            pos=(-0.3, 0.0, 0.5),
            vel=(0.3, 0.0, 0.0),
        ),
        material=gs.materials.Rigid(),
    )
    box2 = scene.add_entity(
        morph=gs.options.morphs.Box(
            size=(0.2, 0.2, 0.2),
            pos=(0.3, 0.0, 0.5),
            vel=(-0.3, 0.0, 0.0),
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build ##########################
    scene.build()

    ########################## simulate ##########################
    for i in range(500):
        scene.step()


if __name__ == "__main__":
    main()
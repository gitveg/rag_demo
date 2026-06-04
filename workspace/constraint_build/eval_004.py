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
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -3.5, 2.5),
            camera_lookat=(0.0, 0.0, 1.0),
            camera_fov=40,
            max_FPS=60,
        ),
        sim_options=gs.options.SimOptions(gravity=(0.0, 0.0, 0.0)),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # Rigid box
    box = scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(0.0, 0.0, 0.5),
            size=(0.5, 0.5, 0.5),
        ),
        material=gs.materials.Rigid(rho=200.0),
    )

    ########################## build ##########################
    scene.build()

    ########################## run ##########################
    for i in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
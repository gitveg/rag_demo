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
        show_viewer=args.vis,
        show_FPS=False,
    )

    ########################## entities ##########################
    # Ground plane
    plane = gs.morphs.Plane()
    scene.add_entity(plane, material=gs.materials.Rigid())

    # Soft elastic cube
    cube = gs.morphs.Box(
        size=(0.2, 0.2, 0.2),
        pos=(0.0, 0.0, 1.0),
    )
    cube_entity = scene.add_entity(cube, material=gs.materials.FEM.Elastic())

    ########################## build ##########################
    scene.build()

    ########################## run ##########################
    for i in range(500):
        scene.step()


if __name__ == "__main__":
    main()
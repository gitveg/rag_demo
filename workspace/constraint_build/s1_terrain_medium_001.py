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
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 3.0, 5.0),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
        show_FPS=True,
    )

    ########################## entities ##########################
    # bumpy terrain with multiple peaks and valleys
    terrain = scene.add_entity(
        morph=gs.options.morphs.Terrain(
            n_subterrains=(2, 2),  # creates 2x2 random hills/valleys
            subterrain_size=(2.0, 2.0),
        ),
    )

    # three rigid spheres at different locations
    sphere_material = gs.materials.Rigid()
    sphere1 = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(-1.5, 1.0, 0.0),
            radius=0.2,
        ),
        material=sphere_material,
    )
    sphere2 = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(0.0, 1.0, 1.5),
            radius=0.2,
        ),
        material=sphere_material,
    )
    sphere3 = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(1.5, 1.0, -1.0),
            radius=0.2,
        ),
        material=sphere_material,
    )

    ########################## build ##########################
    scene.build()

    ########################## simulate ##########################
    for i in range(2000):
        scene.step()

    if args.vis:
        print("Simulation finished. Close the viewer window to exit.")


if __name__ == "__main__":
    main()
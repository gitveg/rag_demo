import argparse
import time

import numpy as np
import torch

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    ########################## create a scene ##########################

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
            constraint_solver=gs.constraint_solver.Newton,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.0, -10.0, 10.0),
            camera_lookat=(4.0, 4.0, 0.0),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    horizontal_scale = 0.25
    vertical_scale = 0.005

    ########################## entities ##########################
    # hilly fractal terrain
    scene.add_entity(
        morph=gs.morphs.Terrain(
            n_subterrains=(1, 1),
            subterrain_size=(8.0, 8.0),
            horizontal_scale=horizontal_scale,
            vertical_scale=vertical_scale,
            subterrain_types=[["fractal_terrain"]],
        ),
    )

    # sphere placed above the center of the terrain
    scene.add_entity(
        morph=gs.morphs.Sphere(
            radius=0.3,
            pos=(4.0, 4.0, 1.0),
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build ##########################
    scene.build()

    ########################## simulate ##########################
    if args.vis:
        # viewer loop
        while scene.viewer.is_alive():
            scene.step()
    else:
        # headless run for a few seconds
        for _ in range(500):
            scene.step()


if __name__ == "__main__":
    main()
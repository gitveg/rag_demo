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
            camera_pos=(-5.0, -5.0, 10.0),
            camera_lookat=(5.0, 5.0, 0.0),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # gently sloped terrain
    terrain = scene.add_entity(
        morph=gs.morphs.Terrain(
            n_subterrains=(1, 1),
            subterrain_types=[["sloped_terrain"]],
        ),
    )

    # rigid sphere placed above the slope
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 2.0),
            radius=0.5,
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build ##########################
    scene.build(n_envs=0)

    ########################## simulation loop ##########################
    for _ in range(1000):
        scene.step()
        # small delay for viewer interactivity (optional)
        # time.sleep(0.001)

    if args.vis:
        # keep viewer open briefly
        time.sleep(2)


if __name__ == "__main__":
    main()
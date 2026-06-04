import argparse
import os

import genesis as gs
import numpy as np
from genesis.utils.terrain import mesh_to_heightfield


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(),
        show_viewer=args.vis,
    )

    ########################## create a terrain ##########################
    terrain_morph = gs.options.morphs.Terrain(
        n_subterrains=(3, 3),
        terrain_config={
            "rand_hill": True,
            "x_valley": True,
            "y_valley": True,
            "h_min": 0.1,
            "h_max": 0.5,
            "vx_scale": 0.1,
            "vy_scale": 0.1,
        },
    )
    terrain = scene.add_entity(
        morph=terrain_morph,
        surface=gs.surfaces.Default(),
    )

    ########################## create a rigid sphere ##########################
    sphere = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(8.0, 0.0, 20.0),
            scale=0.5,
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build the scene ##########################
    scene.build()

    ########################## simulation loop ##########################
    if args.vis:
        scene.viewer.start()
    else:
        for i in range(1000):
            scene.step()


if __name__ == "__main__":
    main()
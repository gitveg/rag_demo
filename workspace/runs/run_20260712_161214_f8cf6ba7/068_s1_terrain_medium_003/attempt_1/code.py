import argparse
import os

import genesis as gs
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -50, 0),
            camera_lookat=(0, 0, 0),
        ),
        show_viewer=args.vis,
    )

    # Create a large terrain with rolling hills and a central slope
    horizontal_scale = 2.0
    vertical_scale = 1.0
    n_subterrains = (3, 3)
    subterrain_size = (5.0, 5.0)
    subterrain_types = [
        ["random_uniform_terrain", "random_uniform_terrain", "random_uniform_terrain"],
        ["random_uniform_terrain", "pyramid_sloped_terrain", "random_uniform_terrain"],
        ["random_uniform_terrain", "random_uniform_terrain", "random_uniform_terrain"],
    ]

    terrain = scene.add_entity(
        morph=gs.morphs.Terrain(
            n_subterrains=n_subterrains,
            subterrain_size=subterrain_size,
            horizontal_scale=horizontal_scale,
            vertical_scale=vertical_scale,
            subterrain_types=subterrain_types,
        ),
    )

    # Place a rigid box above the slope (center sub-terrain)
    box = scene.add_entity(
        morph=gs.morphs.Box(pos=(2.0, 2.0, 10.0), size=(0.5, 0.5, 0.5)),
        material=gs.materials.Rigid(),
    )

    ########################## build ##########################
    scene.build()

    ########################## run simulation ##########################
    for _ in range(2000):
        scene.step()


if __name__ == "__main__":
    main()
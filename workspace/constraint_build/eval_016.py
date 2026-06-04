import argparse
import os

import numpy as np

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu, logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        show_viewer=args.vis,
    )

    ########################## add entities ##########################
    # rigid ground plane
    plane = gs.options.morphs.Plane()
    scene.add_entity(
        morph=plane,
        material=gs.materials.Rigid(),
    )

    # soft elastic bunny mesh
    bunny_morph = gs.options.morphs.Mesh(
        file="meshes/bunny.obj",
        pos=(0.0, 0.5, 0.0),  # position above ground
        scale=0.5,
    )
    bunny_material = gs.materials.PBD.Elastic()
    scene.add_entity(
        morph=bunny_morph,
        material=bunny_material,
    )

    ########################## build ##########################
    scene.build()

    ########################## simulate ##########################
    for i in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
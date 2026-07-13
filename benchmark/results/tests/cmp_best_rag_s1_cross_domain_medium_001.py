import argparse
import os
import sys

import numpy as np
import torch

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="64")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1e-3,
            gravity=(0.0, 0.0, -9.81),
            substeps=2,
        ),
        fem_options=gs.options.FEMOptions(
            dt=1e-3,
            solver="implicit",
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, 0.0, 1.5),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=args.vis,
    )

    ########################## add entities ##########################
    # rigid sphere
    sphere = scene.add_entity(
        gs.options.morphs.Sphere(
            pos=(0.0, 0.0, 1.0),
            radius=0.15,
        ),
        material=gs.materials.Rigid(rho=1000.0),
    )

    # soft elastic sheet (thin box)
    sheet_width = 1.0
    sheet_length = 1.0
    sheet_thickness = 0.02
    sheet = scene.add_entity(
        gs.options.morphs.Box(
            pos=(0.0, 0.0, 0.2),
            size=(sheet_width, sheet_length, sheet_thickness),
        ),
        material=gs.materials.FEM.Elastic(
            E=5e4,
            nu=0.45,
            rho=500.0,
            model="stable_neohookean",
        ),
        surface=gs.options.surfaces.Plastic(color=(0.2, 0.8, 0.2, 1.0)),
    )

    # fix the four bottom corners of the sheet to keep it stretched horizontally
    sheet_node = sheet.get_node()
    # The box morph discretization typically places the 8 corner vertices first.
    # Bottom corners (z = -thickness/2) are vertices 4,5,6,7 (hoping this holds).
    for corner_idx in [4, 5, 6, 7]:
        sheet_node.fix_vertex(corner_idx)

    ########################## build scene ##########################
    scene.build()

    ########################## run simulation ##########################
    for _ in range(2000):
        scene.step()
        if args.vis and _ % 10 == 0:
            print(f"Step {_}")

    ########################## exit ##########################
    gs.exit()


if __name__ == "__main__":
    main()
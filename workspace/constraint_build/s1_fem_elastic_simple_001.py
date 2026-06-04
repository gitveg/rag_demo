import argparse
import sys
import numpy as np
import genesis as gs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    args = parser.parse_args()

    n_steps = 200

    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="64")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=1/60),
        show_viewer=args.vis,
    )

    # Ground: a large rigid sphere
    ground = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            radius=10.0,
            pos=(0.0, 0.0, 0.0),
        ),
        material=gs.materials.Rigid(),
    )

    # Soft elastic ball
    ball = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            radius=0.5,
            pos=(0.0, 13.0, 0.0),
        ),
        material=gs.materials.FEM.Elastic(
            E=1e6,
            nu=0.2,
            rho=1000.0,
            friction_mu=0.1,
        ),
    )

    scene.build()

    for i in range(n_steps):
        scene.step()

if __name__ == "__main__":
    main()
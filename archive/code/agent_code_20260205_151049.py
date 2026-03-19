import argparse
import logging

import numpy as np

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.gpu, logging_level=logging.DEBUG, performance_mode=True)
    dt = 1e-3
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=dt, gravity=(0.0, 0.0, -9.8)),
        coupler_options=gs.options.IPCCouplerOptions(
            dt=dt,
            gravity=(0.0, 0.0, -9.8),
            ipc_constraint_strength=(1, 1),
            IPC_self_contact=False,
        ),
        show_viewer=args.vis,
    )

    scene.add_entity(gs.morphs.Plane())

    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, 0.0, 0.05), size=(1.0, 1.0, 0.1)),
        material=gs.materials.Rigid(),
    )

    scene.add_entity(
        morph=gs.morphs.Sphere(pos=(0.0, 0.0, 0.6), radius=0.5),
        material=gs.materials.Rigid(),
    )

    scene.build()

    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
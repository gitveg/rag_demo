import argparse
import logging

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.gpu, logging_level=logging.DEBUG, performance_mode=True)
    dt = 1e-3
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=dt, gravity=(0.0, -9.8, 0.0)),
        coupler_options=gs.options.IPCCouplerOptions(
            dt=dt,
            gravity=(0.0, -9.8, 0.0),
            ipc_constraint_strength=(1, 1),
            IPC_self_contact=False,
        ),
        show_viewer=args.vis,
    )

    scene.add_entity(gs.morphs.Plane())

    scene.add_entity(
        gs.morphs.Box(pos=(0.0, 0.5, 0.0), size=(0.2, 0.2, 0.2)),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Collision(),
    )

    scene.add_entity(
        gs.morphs.Sphere(pos=(0.1, 1.0, 0.0), radius=0.15),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Collision(),
    )

    scene.build()

    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
import argparse

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
        sim_options=gs.options.SimOptions(
            gravity=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    ball = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.0, 0.0, 0.5),
            radius=0.15,
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build & run ##########################
    scene.build()
    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
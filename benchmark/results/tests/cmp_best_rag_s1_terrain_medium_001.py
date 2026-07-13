import argparse
import time

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(10.0, 0.0, 10.0),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
    )

    ########################## add bumpy terrain ##########################
    # 3x3 grid of subterrains; each cell specifies a terrain type.
    subterrain_types = [
        ["random_uniform_terrain", "wave_terrain", "random_uniform_terrain"],
        ["wave_terrain", "random_uniform_terrain", "wave_terrain"],
        ["random_uniform_terrain", "wave_terrain", "random_uniform_terrain"],
    ]

    terrain = scene.add_entity(
        gs.options.morphs.Terrain(subterrain_types=subterrain_types),
    )

    ########################## add three rigid spheres ##########################
    # Drop them at different locations so they roll into valleys.
    sphere1 = scene.add_entity(
        gs.options.morphs.Sphere(pos=(-3.0, -3.0, 5.0), radius=0.5),
        material=gs.materials.Rigid(),
    )

    sphere2 = scene.add_entity(
        gs.options.morphs.Sphere(pos=(3.0, 3.0, 5.0), radius=0.5),
        material=gs.materials.Rigid(),
    )

    sphere3 = scene.add_entity(
        gs.options.morphs.Sphere(pos=(0.0, 0.0, 5.0), radius=0.5),
        material=gs.materials.Rigid(),
    )

    ########################## build and simulate ##########################
    scene.build()

    for _ in range(1000):
        scene.step()
        if args.vis:
            time.sleep(0.001)   # small pause for easier viewing


if __name__ == "__main__":
    main()
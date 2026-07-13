import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    # initialize genesis
    gs.init(backend=gs.gpu)

    # create scene with basic rigid solver options and a viewer
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

    # terrain parameters
    n_subterrains = (1, 1)
    subterrain_size = (8.0, 8.0)
    horizontal_scale = 0.25
    vertical_scale = 0.005

    # add fractal hilly terrain
    scene.add_entity(
        morph=gs.morphs.Terrain(
            n_subterrains=n_subterrains,
            subterrain_size=subterrain_size,
            horizontal_scale=horizontal_scale,
            vertical_scale=vertical_scale,
            subterrain_types=[["fractal_terrain"]],
        ),
    )

    # add a rigid sphere placed near the center of the terrain (starting above the highest point)
    scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(4.0, 4.0, 2.0),   # center of a 8x8 terrain
            radius=0.3,
            fixed=False,
        ),
        material=gs.materials.Rigid(),
    )

    # build the scene
    scene.build()

    # simulation loop (exit with Ctrl+C)
    try:
        while True:
            scene.step()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
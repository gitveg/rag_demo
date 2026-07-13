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
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # container (fixed)
    container = scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.5),
            size=(1.0, 1.0, 1.0),
            fixed=True,
        ),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5, 1.0)),
    )

    # water (MPM liquid)
    water = scene.add_entity(
        material=gs.materials.MPM.Liquid(rho=1000.0, sampler="regular"),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.25),
            size=(0.8, 0.8, 0.4),
        ),
        surface=gs.surfaces.Default(color=(0.2, 0.6, 1.0, 0.8)),
    )

    # rigid sphere
    sphere = scene.add_entity(
        material=gs.materials.Rigid(rho=500.0),
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 0.9),
            radius=0.1,
        ),
        surface=gs.surfaces.Default(color=(1.0, 0.5, 0.0, 1.0)),
    )

    ########################## build ##########################
    scene.build()

    ########################## simulate ##########################
    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
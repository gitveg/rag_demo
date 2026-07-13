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
    tank = scene.add_entity(
        gs.morphs.Mesh(
            file="meshes/tank.obj",
            scale=5.0,
            fixed=True,
            euler=(90, 0, 0),
        ),
    )

    water = scene.add_entity(
        material=gs.materials.SPH.Liquid(mu=0.01, sampler="regular"),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.3),
            size=(2.0, 2.0, 0.6),
        ),
        surface=gs.surfaces.Default(color=(0.5, 0.7, 0.9, 1.0)),
    )

    ball = scene.add_entity(
        material=gs.materials.Rigid(rho=7800),
        morph=gs.morphs.Sphere(
            radius=0.15,
            pos=(0.0, 0.0, 2.0),
        ),
        surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8)),
    )

    ########################## build and simulate ##########################
    scene.build()

    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
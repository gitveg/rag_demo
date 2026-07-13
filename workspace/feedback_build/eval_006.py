import argparse

import genesis as gs


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 1.5, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # ground plane (fixed)
    ground = scene.add_entity(
        gs.morphs.Plane(fixed=True),
    )

    # two spheres side by side
    radius = 0.2
    sphere1 = scene.add_entity(
        gs.morphs.Sphere(
            pos=(-0.5, 0.0, 1.0),
            radius=radius,
        ),
    )
    sphere2 = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.5, 0.0, 1.0),
            radius=radius,
        ),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## simulation loop ##########################
    if args.vis:
        while True:
            scene.step()
    else:
        for _ in range(1000):
            scene.step()


if __name__ == "__main__":
    main()
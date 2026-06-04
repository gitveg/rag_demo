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
            camera_pos=(4.0, 2.0, 4.0),
            camera_lookat=(0.0, 1.0, 0.0),
        ),
        show_viewer=args.vis,
    )

    ########################## add entities ##########################
    # slanted rigid plane (tilted around x-axis)
    plane_morph = gs.options.morphs.Plane(pos=(0.0, 0.0, 0.0), euler=(0.2, 0.0, 0.0))
    scene.add_entity(morph=plane_morph, material=gs.materials.Rigid())

    # water sphere above the plane
    water_morph = gs.options.morphs.Sphere(pos=(0.0, 3.0, 0.0), radius=0.5)
    scene.add_entity(morph=water_morph, material=gs.materials.MPM.Liquid())

    ########################## build the scene ##########################
    scene.build()

    ########################## run simulation ##########################
    for i in range(500):
        scene.step()


if __name__ == "__main__":
    main()
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
            camera_pos=(1.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=args.vis,
    )

    ########################## add entities ##########################
    # horizontal plane
    plane = scene.add_entity(
        morph=gs.morphs.Plane(),
    )

    # falling cylinder at height 3 meters
    cylinder = scene.add_entity(
        morph=gs.morphs.Cylinder(
            pos=(0.0, 0.0, 3.0),
            radius=0.2,
            height=0.5,
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build ##########################
    scene.build()

    ########################## run simulation ##########################
    for i in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    # initialize
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    # create scene
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, 0.0, 1.5),
            camera_lookat=(0.0, 0.0, 1.0),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    # add two rigid spheres
    sphere1 = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(-0.5, 0.0, 1.0),
            radius=0.1,
        ),
        material=gs.materials.Rigid(),
    )
    sphere2 = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.5, 0.0, 1.0),
            radius=0.1,
        ),
        material=gs.materials.Rigid(),
    )

    # build scene
    scene.build()

    # set initial velocities towards each other
    speed = 0.5
    sphere1.set_dofs_velocity([speed, 0.0, 0.0, 0.0, 0.0, 0.0])
    sphere2.set_dofs_velocity([-speed, 0.0, 0.0, 0.0, 0.0, 0.0])

    # simulate
    for _ in range(300):
        scene.step()

    print("Simulation finished")


if __name__ == "__main__":
    main()
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
    # large static box
    box = scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 0.0),
            size=(2.0, 2.0, 0.2),
            fixed=True,
        ),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 1.0)),
    )

    # small falling sphere
    sphere = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.0, 0.0, 1.0),
            radius=0.1,
        ),
        surface=gs.surfaces.Default(color=(1.0, 0.0, 0.0)),
    )

    ########################## build and simulate ##########################
    scene.build(n_envs=0)

    if args.vis:
        scene.start_recording()

    for _ in range(200):
        scene.step()

    if args.vis:
        scene.viewer.save_video("sphere_falling_on_box.mp4")


if __name__ == "__main__":
    main()
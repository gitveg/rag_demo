import argparse
import numpy as np
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
            camera_pos=(0, -3.5, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
            max_FPS=60,
        ),
        sim_options=gs.options.SimOptions(
            dt=0.01,
        ),
        show_viewer=args.vis,
        show_FPS=False,
    )

    ########################## entities ##########################
    plane = scene.add_entity(gs.morphs.Plane())

    # Sphere with gravity compensation: cancels gravity, hovers in place
    sphere = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0, 0, 0.5),
            radius=0.2,
        ),
        material=gs.materials.Rigid(gravity_compensation=1.0),
    )

    ########################## build and simulate ##########################
    scene.build()

    if args.vis:
        try:
            while True:
                scene.step()
        except KeyboardInterrupt:
            pass
    else:
        for _ in range(500):
            scene.step()


if __name__ == "__main__":
    main()
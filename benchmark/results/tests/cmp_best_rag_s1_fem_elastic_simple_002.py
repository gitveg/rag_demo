import argparse
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -3.5, 2.5),
            camera_lookat=(0.0, 0.0, 1.0),
            camera_fov=40,
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # ground plane
    plane = scene.add_entity(gs.morphs.Plane())

    # soft elastic cube falling from air
    cube = scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 1.0),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.FEM.Elastic(),
    )

    scene.build()

    # run simulation for a few seconds
    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
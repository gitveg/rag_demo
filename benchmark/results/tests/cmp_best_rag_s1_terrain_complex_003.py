import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5.0, 5.0, 5.0),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
        renderer=gs.renderers.RayTracer(),
    )

    # Static terrain mesh as the rigid surface
    scene.add_entity(
        gs.morphs.Mesh(
            file="meshes/terrain_45.obj",
            pos=(0, 0, 0),
        ),
        surface=gs.surfaces.Default(color=(0.5, 0.4, 0.3)),
    )

    # Ball placed above the terrain
    scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.0, 0.0, 2.0),
            radius=0.15,
        ),
        surface=gs.surfaces.Default(color=(0.2, 0.6, 0.8)),
    )

    scene.build()

    for _ in range(2000):
        scene.step()


if __name__ == "__main__":
    main()
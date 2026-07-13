import torch

import genesis as gs


def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -3, 2),
            camera_lookat=(0, 0, 1.5),
        ),
    )

    # Ground plane
    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5)),
    )

    # Red rigid box
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0, 0, 3),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(1.0, 0.0, 0.0)),
    )

    # Blue rigid cylinder
    scene.add_entity(
        morph=gs.morphs.Cylinder(
            pos=(0.3, 0, 3),
            radius=0.1,
            height=0.2,
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.0, 0.0, 1.0)),
    )

    scene.build()

    for _ in range(2000):
        scene.step()


if __name__ == "__main__":
    main()
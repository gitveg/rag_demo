import argparse

import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.5, -1.5, 1.5),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
    )

    scene.add_entity(morph=gs.morphs.Plane())

    red_plastic = scene.add_entity(
        morph=gs.morphs.Box(size=(0.2, 0.2, 0.2), pos=(-0.3, 0.0, 0.1)),
        surface=gs.surfaces.Rough(color=(0.9, 0.1, 0.1, 1.0)),
    )

    rough_concrete = scene.add_entity(
        morph=gs.morphs.Box(size=(0.2, 0.2, 0.2), pos=(0.0, 0.0, 0.1)),
        surface=gs.surfaces.Rough(color=(0.6, 0.6, 0.6, 1.0)),
    )

    polished_gold = scene.add_entity(
        morph=gs.morphs.Box(size=(0.2, 0.2, 0.2), pos=(0.3, 0.0, 0.1)),
        surface=gs.surfaces.Gold(),
    )

    scene.build()

    for i in range(200):
        scene.step()


if __name__ == "__main__":
    main()
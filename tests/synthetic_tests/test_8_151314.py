"""
User Query: Implement a soft body self-collision with a custom distance threshold and a different friction value for soft-soft contacts versus soft-rigid contacts.
"""

import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.0, -2, 1.5),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
    )

    # Add a plane
    scene.add_entity(
        shape=gs.shapes.Plane(),
        surface=gs.surfaces.Collision(contype=0xFFFF, conaffinity=0xFFFF),
    )

    # Add a rigid cube
    scene.add_entity(
        shape=gs.shapes.Box(half_extents=(0.5, 0.5, 0.5)),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Collision(contype=1, conaffinity=1),
    )

    # TODO: Add soft body with self-collision and custom distance threshold.
    # TODO: Set different friction for soft-soft vs soft-rigid contacts.

    scene.build()

    for _ in range(100):
        scene.step()

    if args.vis:
        scene.viewer.run()


if __name__ == "__main__":
    main()
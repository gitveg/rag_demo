import genesis as gs


def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(show_viewer=True)

    # Static ground plane
    scene.add_entity(gs.morphs.Plane())

    # Three boxes stacked vertically
    box_height = 0.5
    # Bottom box sits on plane (z=0) with center at half_height
    scene.add_entity(gs.morphs.Box(size=(0.5, 0.5, 0.5), pos=(0.0, 0.0, box_height / 2)))
    # Middle box center at 3 * half_height
    scene.add_entity(gs.morphs.Box(size=(0.5, 0.5, 0.5), pos=(0.0, 0.0, 3 * box_height / 2)))
    # Top box center at 5 * half_height
    scene.add_entity(gs.morphs.Box(size=(0.5, 0.5, 0.5), pos=(0.0, 0.0, 5 * box_height / 2)))

    scene.build()

    # Run simulation for a few seconds to let the boxes settle
    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
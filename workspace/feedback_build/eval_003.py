import argparse
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    # Initialize Genesis
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    # Create scene
    scene = gs.Scene(
        show_viewer=args.vis,
    )

    # Add a horizontal plane (static by default)
    scene.add_entity(gs.morphs.Plane())

    # Add a rigid cylinder placed at 3 meters above the plane
    scene.add_entity(
        gs.morphs.Cylinder(
            height=1.0,       # cylinder length
            radius=0.5,       # cylinder radius
            pos=(0.0, 0.0, 3.0),  # center at z=3 m
            fixed=False,      # free to fall
        ),
    )

    # Build the scene (must be called before stepping)
    scene.build()

    # Run simulation for a few seconds
    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
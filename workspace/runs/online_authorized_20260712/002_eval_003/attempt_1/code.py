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
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, 3, 3),
            camera_lookat=(0, 0, 1),
        ),
        show_viewer=args.vis,
    )

    # Add horizontal plane (fixed by default)
    scene.add_entity(gs.morphs.Plane())

    # Add a rigid cylinder dropped from 3 meters above the plane
    scene.add_entity(
        gs.morphs.Cylinder(
            height=0.5,
            radius=0.3,
            pos=(0, 0, 3),
        ),
    )

    # Build the scene
    scene.build()

    # Run the simulation
    while True:
        scene.step()

if __name__ == "__main__":
    main()
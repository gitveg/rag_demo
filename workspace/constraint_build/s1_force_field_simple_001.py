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
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=args.vis,
    )

    # Rigid sphere – will fall and be pushed sideways by wind
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(radius=0.2, pos=(0.0, 0.0, 1.0)),
        material=gs.materials.Rigid(),
    )

    # Constant wind pushing along +x direction, with large radius to cover fall
    wind = gs.force_fields.Wind(direction=(1.0, 0.0, 0.0), strength=5.0, radius=10.0, center=(0.0, 0.0, 1.0))
    scene.add_force_field(wind)

    scene.build()

    for i in range(1000):
        scene.step()

if __name__ == "__main__":
    main()
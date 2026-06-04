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

    # material with default gravity
    mat_default = gs.materials.Rigid()
    # material with upward force: compensate gravity (2x => net upward 1g)
    mat_float = gs.materials.Rigid(gravity_compensation=2.0)

    # left sphere – lower height
    scene.add_entity(
        morph=gs.options.morphs.Sphere(pos=(-1.0, 0.0, 0.5), radius=0.2),
        material=mat_default,
    )
    # middle sphere – medium height, floats upward
    scene.add_entity(
        morph=gs.options.morphs.Sphere(pos=(0.0, 0.0, 2.0), radius=0.2),
        material=mat_float,
    )
    # right sphere – higher height
    scene.add_entity(
        morph=gs.options.morphs.Sphere(pos=(1.0, 0.0, 3.0), radius=0.2),
        material=mat_default,
    )

    scene.build()

    for _ in range(1000):
        scene.step()

if __name__ == "__main__":
    main()
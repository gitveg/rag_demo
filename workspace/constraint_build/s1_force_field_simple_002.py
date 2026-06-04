import argparse
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
    )

    ########################## add a lightweight sphere ##########################
    sphere = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            radius=0.3,
            pos=(0.0, 0.0, 1.0),
        ),
        material=gs.materials.Rigid(rho=1.0),  # lightweight
    )

    ########################## add wind force field ##########################
    wind = gs.force_fields.Wind(
        direction=(1.0, 0.0, 0.0),  # sideways
        strength=10.0,
        radius=2.0,
        center=(0.0, 0.0, 1.0),
    )
    scene.add_force_field(wind)

    ########################## build the scene ##########################
    scene.build()

    ########################## simulate ##########################
    for i in range(300):
        scene.step()


if __name__ == "__main__":
    main()
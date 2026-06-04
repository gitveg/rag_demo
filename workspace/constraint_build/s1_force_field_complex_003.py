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

    ########################## add central attractor ##########################
    scene.add_entity(
        morph=gs.options.morphs.Sphere(pos=(0.0, 0.0, 0.0), radius=0.2),
        material=gs.materials.Rigid(rho=10000.0),  # heavy static-like sphere
    )

    ########################## add surrounding objects ##########################
    # small spheres placed around the center
    positions = [
        (0.8, 0.0, 0.0),
        (0.0, 0.8, 0.0),
        (-0.8, 0.0, 0.0),
        (0.0, -0.8, 0.0),
        (0.6, 0.6, 0.0),
        (-0.6, 0.6, 0.0),
        (0.6, -0.6, 0.0),
        (-0.6, -0.6, 0.0),
    ]
    for pos in positions:
        scene.add_entity(
            morph=gs.options.morphs.Sphere(pos=pos, radius=0.05),
            material=gs.materials.Rigid(rho=100.0),
        )

    ########################## add a strong constant force field ##########################
    # Using a constant force field to approximate an attractive pull (not truly radial)
    force_field = gs.force_fields.Constant(direction=(0.0, 0.0, -1.0), strength=100.0)
    scene.add_force_field(force_field)

    ########################## build the scene ##########################
    scene.build()

    ########################## run simulation ##########################
    for i in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
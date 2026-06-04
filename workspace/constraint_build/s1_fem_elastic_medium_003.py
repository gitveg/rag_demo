import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
    )

    # Ground plane
    plane = gs.options.morphs.Plane()
    scene.add_entity(plane, material=gs.materials.Rigid())

    # Three squishy elastic spheres of different sizes
    sphere_material = gs.materials.FEM.Elastic(
        E=50000.0, nu=0.4, rho=1000.0
    )
    sphere_positions = [(-0.8, 1.0, 0.0), (0.0, 1.0, 0.0), (0.8, 1.0, 0.0)]
    sphere_radii = [0.25, 0.35, 0.45]

    for pos, radius in zip(sphere_positions, sphere_radii):
        sphere = gs.options.morphs.Sphere(
            pos=pos,
            radius=radius,
        )
        scene.add_entity(sphere, material=sphere_material)

    # Build the scene
    scene.build()

    # Run simulation
    for i in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
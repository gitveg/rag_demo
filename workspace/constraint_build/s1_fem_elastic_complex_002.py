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
            camera_pos=(3.0, 0.0, 3.0),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=args.vis,
    )

    # Soft bunny (large sphere with FEM elastic material)
    bunny = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(0.0, 1.0, 0.0),
            radius=0.5,
        ),
        material=gs.materials.FEM.Elastic(
            E=1e5, nu=0.45, rho=500.0
        ),
    )

    # Platform (large static sphere made of very dense rigid material)
    platform = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(0.0, -0.5, 0.0),
            radius=1.5,
        ),
        material=gs.materials.Rigid(
            rho=1e6,
        ),
    )

    # Metal spheres
    sphere_1 = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(0.0, 2.5, 0.0),
            radius=0.1,
        ),
        material=gs.materials.Rigid(
            rho=7800.0,
        ),
    )
    sphere_2 = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(0.3, 3.0, 0.2),
            radius=0.1,
        ),
        material=gs.materials.Rigid(
            rho=7800.0,
        ),
    )
    sphere_3 = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(-0.2, 2.0, -0.3),
            radius=0.1,
        ),
        material=gs.materials.Rigid(
            rho=7800.0,
        ),
    )

    scene.build()

    for i in range(500):
        scene.step()

if __name__ == "__main__":
    main()
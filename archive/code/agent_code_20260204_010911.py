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
        sim_options=gs.options.SimOptions(
            substeps=4,
        ),
        rigid_options=gs.options.RigidOptions(
            gravity=(0, 0, -9.8),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, 2.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.0),
            camera_fov=50,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # ground
    ground = scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, -0.05),
            size=(10.0, 10.0, 0.1),
            fixed=True,
        )
    )

    # sphere
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 1.0),
            radius=0.1,
        ),
        material=gs.materials.Rigid(rho=1000.0),
    )

    ########################## build & run ##########################
    scene.build()
    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
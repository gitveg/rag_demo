import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu, logging_level="info")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            substeps=10,
            gravity=(0, 0, -9.8),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, 1.5, 1.0),
            camera_lookat=(0, 0, 0.2),
            camera_up=(0, 0, 1),
        ),
        show_viewer=args.vis,
    )

    # materials
    mat_elastic = gs.materials.PBD.Elastic()
    mat_rigid_metal = gs.materials.Rigid(rho=7800.0)

    # ground plane
    scene.add_entity(gs.morphs.Plane())

    # soft bunny
    scene.add_entity(
        morph=gs.morphs.Mesh(
            file="meshes/bunny.obj",
            pos=(0.0, 0.0, 0.1),
        ),
        material=mat_elastic,
    )

    # falling rigid metal spheres
    sphere_positions = [
        (0.0, 0.0, 0.5),
        (0.2, 0.2, 0.6),
        (-0.15, -0.15, 0.7),
        (0.1, -0.2, 0.65),
        (-0.2, 0.1, 0.75),
    ]
    for pos in sphere_positions:
        scene.add_entity(
            morph=gs.morphs.Sphere(
                pos=pos,
                radius=0.04,
            ),
            material=mat_rigid_metal,
        )

    scene.build()

    # simulation loop – enough time to compress and settle
    for i in range(5000):
        scene.step()


if __name__ == "__main__":
    main()
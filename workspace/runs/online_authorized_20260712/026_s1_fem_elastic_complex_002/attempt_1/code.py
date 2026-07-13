import argparse
import numpy as np

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu, logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            substeps=10,
            gravity=(0, 0, -9.8),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2, 2, 1.5),
            camera_lookat=(0, 0, 0.5),
            camera_up=(0, 0, 1),
        ),
        show_viewer=args.vis,
    )

    ########################## materials ##########################
    mat_elastic = gs.materials.PBD.Elastic()
    mat_metal = gs.materials.Rigid(rho=8000.0)

    ########################## entities ##########################
    # platform
    scene.add_entity(gs.morphs.Plane())

    # Stanford bunny as soft elastic body
    scene.add_entity(
        morph=gs.morphs.Mesh(
            file="meshes/bunny.obj",
            pos=(0, 0, 0),
        ),
        material=mat_elastic,
        surface=gs.surfaces.Default(color=(0.8, 0.6, 0.4, 1.0)),
    )

    # several rigid metal spheres dropped from different heights
    sphere_radius = 0.05
    sphere_positions = [
        ( 0.3,  0.0, 0.6),
        (-0.2,  0.2, 0.7),
        ( 0.0, -0.25, 0.55),
        (-0.25, -0.2, 0.65),
        ( 0.2, -0.1, 0.75),
    ]
    for pos in sphere_positions:
        scene.add_entity(
            morph=gs.morphs.Sphere(
                pos=pos,
                radius=sphere_radius,
            ),
            material=mat_metal,
            surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5, 1.0)),
        )

    ########################## build ##########################
    scene.build()

    ########################## simulation loop ##########################
    for _ in range(500):
        scene.step()

    if args.vis:
        scene.viewer.close()


if __name__ == "__main__":
    main()
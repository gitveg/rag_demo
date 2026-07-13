import argparse
import numpy as np
import genesis as gs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.gpu, logging_level="info")

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

    ########################## entities ##########################
    # Soft elastic bunny mesh (falling)
    scene.add_entity(
        morph=gs.morphs.Mesh(
            file='bunny.obj',   # Ensure this mesh file exists in the working directory
            pos=(0.0, 0.0, 1.0),
            scale=0.5,          # Adjust if bunny is too large/small
        ),
        material=mat_elastic,
    )

    # Rigid ground plane (fixed)
    scene.add_entity(
        morph=gs.morphs.Plane(
            pos=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build and simulate ##########################
    scene.build()

    for _ in range(200):
        scene.step()

if __name__ == "__main__":
    main()
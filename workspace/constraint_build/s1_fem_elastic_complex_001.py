import argparse
import sys
import numpy as np
import genesis as gs
import os
from huggingface_hub import snapshot_download

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="64")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=1/60),
        vis_options=gs.options.VisOptions(show_world_frame=True),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -1, 1.5),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
        show_FPS=True,
    )

    # Download a mesh dataset (includes a cube mesh for the beam)
    dataset_dir = snapshot_download(repo_id="Genesis/Genesis", repo_type="dataset")
    mesh_path = os.path.join(dataset_dir, "meshes", "cube.obj")

    # Soft elastic beam (made from a cube mesh, fixed at one end via morph placement)
    beam_morph = gs.options.morphs.Mesh(
        file=mesh_path,
        pos=(0.0, 0.0, 0.0),
        eul=(0.0, 0.0, 0.0),
    )
    beam_material = gs.materials.FEM.Elastic(
        E=1e5,
        nu=0.45,
        rho=1000.0,
    )
    beam = scene.add_entity(
        morph=beam_morph,
        material=beam_material,
    )

    # Soft elastic sphere
    sphere_morph = gs.options.morphs.Sphere(
        radius=0.15,
        pos=(0.8, 0.0, 0.3),
    )
    sphere_material = gs.materials.FEM.Elastic(
        E=1e5,
        nu=0.45,
        rho=1000.0,
    )
    sphere = scene.add_entity(
        morph=sphere_morph,
        material=sphere_material,
    )

    # Build the scene
    scene.build()

    # Run simulation
    for i in range(500):
        scene.step()

if __name__ == "__main__":
    main()
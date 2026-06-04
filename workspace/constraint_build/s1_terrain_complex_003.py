import argparse
import os

import genesis as gs
import numpy as np
import trimesh
from genesis.utils.terrain import mesh_to_heightfield


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    parser.add_argument("-m", "--mesh", type=str, default="mountain.obj",
                        help="Path to the terrain mesh file")
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    ########################## load terrain mesh ##########################
    if not os.path.isfile(args.mesh):
        raise FileNotFoundError(f"Mesh file not found: {args.mesh}")
    mesh = trimesh.load(args.mesh, force="mesh")
    # Convert to heightfield
    heightfield, hf_meta = mesh_to_heightfield(mesh)

    ########################## create scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -3, 4),
            camera_lookat=(0, 0, 0.5),
        ),
        show_viewer=args.vis,
        show_FPS=args.vis,
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
        ),
    )

    ########################## add terrain ##########################
    terrain = scene.add_entity(
        morph=gs.morphs.Terrain(
            heightfield=heightfield,
            hf_meta=hf_meta,
        ),
        material=gs.materials.Rigid(
            friction=0.5,
        ),
    )

    ########################## determine peak position ##########################
    # Get maximum height from mesh vertices
    vertices = mesh.vertices
    max_z = np.max(vertices[:, 2])
    min_z = np.min(vertices[:, 2])
    # Center of terrain in xy (assuming mesh centered at origin? We'll compute centroid)
    center_xy = np.mean(vertices[:, :2], axis=0)
    # Place ball slightly above the peak
    ball_pos = (float(center_xy[0]), float(center_xy[1]), float(max_z + 0.5))

    ########################## add rigid ball ##########################
    ball = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=ball_pos,
            radius=0.2,
        ),
        material=gs.materials.Rigid(
            rho=500.0,
            friction=0.3,
        ),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## simulation loop ##########################
    for i in range(1000):
        scene.step()

    ########################## optional: visualize final state ##########################
    if args.vis:
        gs.tools.viewer_camera_auto_pose(scene, ball)

    print("Simulation finished.")


if __name__ == "__main__":
    main()
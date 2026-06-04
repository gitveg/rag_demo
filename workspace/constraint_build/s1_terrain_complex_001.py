import argparse
import os
import numpy as np
import trimesh
import genesis as gs
from genesis.utils.terrain import mesh_to_heightfield


def create_cliff_slope_mesh():
    """
    Create a triangle mesh representing a terrain with a steep cliff on one side
    and a gentle slope on the other.
    """
    # Define grid
    nx, ny = 101, 51
    x = np.linspace(-5, 5, nx)
    y = np.linspace(-5, 5, ny)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros_like(X)

    # Steep cliff at x=0: flat for x<0, then sudden rise
    mask_cliff_left = X < 0
    Z[mask_cliff_left] = 0.0  # left side flat at 0

    # Cliff face: a vertical step from 0 to 2 at x=0 (sharp edge)
    # We'll make it sharp by having a thin strip of vertical faces
    # For simplicity, define a ramp very steep near x=0

    # Gentle slope on right side: linear from 2 at x=0 down to 0 at x=5
    mask_slope = X >= 0
    Z[mask_slope] = 2.0 * (1 - X[mask_slope] / 5.0)

    # Build mesh vertices and faces
    vertices = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=-1)
    faces = []
    for i in range(ny - 1):
        for j in range(nx - 1):
            v0 = i * nx + j
            v1 = i * nx + j + 1
            v2 = (i + 1) * nx + j
            v3 = (i + 1) * nx + j + 1
            faces.append([v0, v1, v2])
            faces.append([v1, v3, v2])

    faces = np.array(faces)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    return mesh


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
            camera_pos=(5, 5, 10),
            camera_lookat=(0, 0, 0),
        ),
        show_viewer=args.vis,
    )

    ########################## create terrain ##########################
    # Generate cliff-slope mesh
    terrain_mesh = create_cliff_slope_mesh()

    # Add terrain entity using the mesh
    terrain = scene.add_entity(
        morph=gs.morphs.Terrain(mesh=terrain_mesh),
        material=gs.materials.Rigid(rho=200.0, friction=0.5),
    )

    ########################## add box (rigid) ##########################
    # Place box at the top of the cliff (left side, near edge)
    box = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(-0.5, 0.0, 2.0),
            scale=(0.3, 0.3, 0.3),
        ),
        material=gs.materials.Rigid(rho=100.0, friction=0.3),
    )

    ########################## add sphere (rigid) ##########################
    # Place sphere at the top of the gentle slope (right side, near cliff)
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.5, 0.0, 2.0),
            scale=0.3,
        ),
        material=gs.materials.Rigid(rho=100.0, friction=0.1),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## simulation loop ##########################
    for i in range(1000):
        scene.step()
        if args.vis:
            # The viewer is updated automatically
            pass


if __name__ == "__main__":
    main()
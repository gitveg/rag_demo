import argparse
import os

import genesis as gs
import numpy as np
from genesis.utils.terrain import mesh_to_heightfield


def generate_hilly_mesh(size=50, num_hills=5):
    # Create a grid of vertices
    x = np.linspace(-5, 5, size)
    y = np.linspace(-5, 5, size)
    xx, yy = np.meshgrid(x, y)
    zz = np.zeros_like(xx)

    # Add hill-like sine waves
    for i in range(num_hills):
        cx = np.random.uniform(-4, 4)
        cy = np.random.uniform(-4, 4)
        height = np.random.uniform(0.5, 1.5)
        sigma = np.random.uniform(1.0, 2.0)
        zz += height * np.exp(-((xx - cx)**2 + (yy - cy)**2) / (2 * sigma**2))

    # Build mesh vertices (Nx3) and faces (triangles)
    vertices = np.stack([xx.ravel(), yy.ravel(), zz.ravel()], axis=1)

    # Generate faces (two triangles per grid cell)
    faces = []
    for j in range(size - 1):
        for i in range(size - 1):
            idx = j * size + i
            # triangle 1
            faces.append([idx, idx + 1, idx + size])
            # triangle 2
            faces.append([idx + 1, idx + size + 1, idx + size])
    faces = np.array(faces)

    # Create a trimesh object (genesis uses trimesh internally)
    import trimesh
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    return mesh


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5, 5, 8),
            camera_lookat=(0, 0, 1),
        ),
        show_viewer=args.vis,
        show_FPS=False,
    )

    # Generate hilly mesh and convert to heightfield
    mesh = generate_hilly_mesh(size=50, num_hills=5)
    heightfield = mesh_to_heightfield(mesh)
    hfield_res = heightfield.shape

    # Add terrain
    terrain = scene.add_entity(
        morph=gs.options.morphs.Terrain(
            heightfield=heightfield,
            hfield_resolution=hfield_res,
            pos=(0, 0, 0),
            euler=(0, 0, 0),
        ),
        material=gs.materials.Rigid(rho=1000, friction=0.3),
    )

    # Find highest point of terrain
    max_h = np.max(heightfield)
    max_idx = np.unravel_index(np.argmax(heightfield), heightfield.shape)
    # Convert grid index to world position (approximately)
    # Terrain is centered at (0,0,0) and spans from -5 to 5 in x and y
    world_x = -5 + (max_idx[1] / (hfield_res[1] - 1)) * 10
    world_y = -5 + (max_idx[0] / (hfield_res[0] - 1)) * 10
    spawn_pos = (world_x, world_y, max_h + 0.5)

    # Add sphere
    sphere = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=spawn_pos,
            radius=0.3,
        ),
        material=gs.materials.Rigid(rho=2000, friction=0.5),
    )

    scene.build()

    for i in range(2000):
        scene.step()

    if args.vis:
        while gs.tools.viewer.is_alive(scene):
            scene.step()


if __name__ == "__main__":
    main()
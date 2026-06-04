import argparse
import numpy as np
import trimesh
import genesis as gs
from genesis.utils.terrain import mesh_to_heightfield


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
            camera_pos=(5.0, 5.0, 10.0),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
        show_FPS=True,
    )

    ########################## create uneven rocky terrain ##########################
    # Generate heightfield with hills and valleys
    nx, ny = 128, 128
    x = np.linspace(-2.0, 2.0, nx)
    y = np.linspace(-2.0, 2.0, ny)
    X, Y = np.meshgrid(x, y, indexing='ij')
    # Combine multiple sine waves for irregular terrain
    Z = (0.3 * np.sin(3.0 * X) * np.cos(3.0 * Y) +
         0.2 * np.sin(5.0 * X + 1.5) * np.cos(4.0 * Y - 1.2) +
         0.1 * np.sin(7.0 * X + 2.7) * np.cos(6.0 * Y + 0.8))
    # Add some sharper features
    Z += 0.15 * np.exp(-((X-0.5)**2 + (Y+0.5)**2) / 0.2)
    Z -= 0.1 * np.exp(-((X+0.8)**2 + (Y-0.3)**2) / 0.1)
    Z -= 0.05 * np.exp(-((X-1.0)**2 + (Y+1.0)**2) / 0.15)
    Z = Z - Z.min()  # shift up so terrain is above plane

    # Create a trimesh from heightfield (needed for mesh_to_heightfield)
    vertices = np.zeros((nx * ny, 3))
    vertices[:, 0] = X.ravel()
    vertices[:, 1] = Y.ravel()
    vertices[:, 2] = Z.ravel()
    faces = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            v0 = i * ny + j
            v1 = i * ny + j + 1
            v2 = (i + 1) * ny + j
            v3 = (i + 1) * ny + j + 1
            faces.append([v0, v1, v2])
            faces.append([v1, v3, v2])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

    # Convert mesh to heightfield array
    heightfield = mesh_to_heightfield(mesh)

    # Create terrain morph from heightfield
    terrain_morph = gs.morphs.Terrain(
        heightfield=heightfield,
        width=4.0,
        depth=4.0,
    )
    terrain = scene.add_entity(
        morph=terrain_morph,
        material=gs.materials.Rigid(),
    )

    ########################## drop several rigid cubes ##########################
    cube_material = gs.materials.Rigid(rho=500.0)
    cube_positions = [
        (-1.0, -0.5, 1.0),
        (0.0, 0.0, 1.0),
        (1.2, 0.3, 1.0),
        (-0.5, 1.0, 1.0),
        (0.8, -0.8, 1.0),
    ]
    for pos in cube_positions:
        cube = scene.add_entity(
            morph=gs.morphs.Box(
                size=(0.3, 0.3, 0.3),
                pos=pos,
            ),
            material=cube_material,
        )

    ########################## build scene ##########################
    scene.build()

    ########################## run simulation ##########################
    for i in range(500):
        scene.step()


if __name__ == "__main__":
    main()
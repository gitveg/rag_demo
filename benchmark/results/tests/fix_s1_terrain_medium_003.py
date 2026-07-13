import argparse
import os
import tempfile

import numpy as np

import genesis as gs


def create_terrain_obj(size, resolution, height_fn, path):
    """Generate an OBJ file for a terrain mesh."""
    nx, ny = resolution
    Lx, Ly = size

    # Grid coordinates
    x = np.linspace(-Lx / 2, Lx / 2, nx)
    y = np.linspace(-Ly / 2, Ly / 2, ny)
    X, Y = np.meshgrid(x, y, indexing="xy")
    Z = height_fn(X, Y)

    vertices = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)

    with open(path, "w") as f:
        # Write vertices
        for v in vertices:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

        # Write faces (two triangles per quad)
        for i in range(nx - 1):
            for j in range(ny - 1):
                idx = i * ny + j + 1  # 1-indexed
                # triangle 1
                f.write(f"f {idx} {idx + 1} {idx + ny + 1}\n")
                # triangle 2
                f.write(f"f {idx} {idx + ny + 1} {idx + ny}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    # Initialize
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    # Terrain parameters
    terrain_size = (20.0, 20.0)
    nx, ny = 150, 150   # grid resolution

    # Height function: large central hill with rolling undulations
    def height_map(X, Y):
        R2 = X**2 + Y**2
        # main hill
        h = 5.0 * np.exp(-R2 / 80.0) + 1.0 * np.sin(0.5 * X) * np.cos(0.5 * Y)
        h = np.maximum(h, 0.1)  # ensure non-negative
        return h

    # Generate a temporary OBJ file for the terrain
    fd, tmp_path = tempfile.mkstemp(suffix=".obj", text=True)
    os.close(fd)
    create_terrain_obj(terrain_size, (nx, ny), height_map, tmp_path)

    # Create the scene
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(8, -14, 8),
            camera_lookat=(0, 0, 3),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    # Add terrain as a mesh
    terrain = scene.add_entity(
        gs.morphs.Mesh(
            file=tmp_path,
            pos=(0, 0, 0),
        ),
    )

    # Place a rigid box on a slope, initially slightly above the surface
    box_half = 0.25
    # find terrain height at (4, 0)
    x_target, y_target = 4.0, 0.0
    # interpolate height from the same grid for accurate placement
    x_vals = np.linspace(-terrain_size[0] / 2, terrain_size[0] / 2, nx)
    y_vals = np.linspace(-terrain_size[1] / 2, terrain_size[1] / 2, ny)
    dx = x_vals[1] - x_vals[0]
    dy = y_vals[1] - y_vals[0]
    ix = max(0, min(int((x_target - x_vals[0]) / dx), nx - 2))
    iy = max(0, min(int((y_target - y_vals[0]) / dy), ny - 2))
    fx = (x_target - x_vals[ix]) / dx
    fy = (y_target - y_vals[iy]) / dy
    H_grid = height_map(
        np.array([[x_vals[ix], x_vals[ix + 1]]]),
        np.array([[y_vals[iy], y_vals[iy + 1]]]),
    )  # not needed, compute directly
    H00 = height_map(x_vals[ix], y_vals[iy])
    H10 = height_map(x_vals[ix + 1], y_vals[iy])
    H01 = height_map(x_vals[ix], y_vals[iy + 1])
    H11 = height_map(x_vals[ix + 1], y_vals[iy + 1])
    z_terrain = (H00 * (1 - fx) * (1 - fy) +
                 H10 * fx * (1 - fy) +
                 H01 * (1 - fx) * fy +
                 H11 * fx * fy)

    box_z = z_terrain + box_half + 0.5  # small drop to gain momentum
    box_pos = np.array([x_target, y_target, box_z])
    box = scene.add_entity(
        gs.morphs.Box(
            pos=box_pos,
            size=(0.5, 0.5, 0.5),
        ),
    )

    # Build the simulation
    scene.build()

    # Clean up the temporary mesh file after it has been loaded
    os.unlink(tmp_path)

    # Run simulation
    steps = 1000
    for _ in range(steps):
        scene.step()

    if args.vis:
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
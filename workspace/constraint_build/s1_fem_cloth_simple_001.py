import argparse
import numpy as np
import genesis as gs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    parser.add_argument("--horizon", type=int, default=300)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    ########################## create scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1e-2,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, 0.5, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=args.vis,
    )

    ########################## create a rigid box ##########################
    box = scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(0.0, 0.0, 0.3),
            size=(0.6, 0.6, 0.6),
        ),
        material=gs.materials.Rigid(),
    )

    ########################## create cloth above the box ##########################
    # Create a rectangular sheet mesh for the cloth
    nx, ny = 20, 20
    dx, dy = 0.6 / nx, 0.6 / ny
    vertices = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = -0.3 + i * dx
            z = -0.3 + j * dy
            vertices.append([x, 1.0, z])  # elevated above box
    vertices = np.array(vertices, dtype=np.float32)

    # Four quadrilateral per cell -> two triangles per quad
    faces = []
    for j in range(ny):
        for i in range(nx):
            i0 = j * (nx + 1) + i
            i1 = i0 + 1
            i2 = (j + 1) * (nx + 1) + i
            i3 = i2 + 1
            faces.append([i0, i1, i2])
            faces.append([i1, i3, i2])
    faces = np.array(faces, dtype=np.int32)

    cloth = scene.add_entity(
        morph=gs.options.morphs.Mesh(
            vertices=vertices,
            faces=faces,
        ),
        material=gs.materials.FEM.Cloth(),
    )

    ########################## build the scene ##########################
    scene.build()

    ########################## simulate ##########################
    for i in range(args.horizon):
        scene.step()

if __name__ == "__main__":
    main()
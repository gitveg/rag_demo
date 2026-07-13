import genesis as gs
import tempfile
import os
import numpy as np


def create_square_cloth_mesh():
    """Generate a 1x1 horizontal square cloth mesh (y=0) with a grid of vertices."""
    n = 11  # resolution
    xs = np.linspace(-0.5, 0.5, n)
    zs = np.linspace(-0.5, 0.5, n)

    vertices = []
    for z in zs:
        for x in xs:
            vertices.append((x, 0.0, z))

    faces = []
    # 1‑based OBJ indexing
    for i in range(n - 1):
        for j in range(n - 1):
            v1 = i * n + j + 1
            v2 = i * n + j + 2
            v3 = (i + 1) * n + j + 2
            v4 = (i + 1) * n + j + 1
            # two triangles per quad
            faces.append((v1, v2, v3))
            faces.append((v1, v3, v4))

    obj = "\n".join(
        ["v {} {} {}".format(*v) for v in vertices]
        + ["f {} {} {}".format(*f) for f in faces]
    )
    return obj


def main():
    # initialization
    gs.init()

    # generate temporary mesh file for the fabric
    mesh_content = create_square_cloth_mesh()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".obj", delete=False) as f:
        f.write(mesh_content)
        mesh_path = f.name

    # create scene
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=2e-3,
            substeps=10,
        ),
        pbd_options=gs.options.PBDOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, -1.5, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=True,
    )

    # static floor
    scene.add_entity(gs.morphs.Plane())

    # square fabric, suspended in the air
    cloth = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=mesh_path,
            pos=(0.0, 0.0, 1.5),  # 1.5 m above the floor
            euler=(0.0, 0.0, 0.0),  # already horizontal
        ),
        material=gs.materials.PBD.Cloth(),
    )

    scene.build()

    # simulate until the fabric comes to rest
    for _ in range(500):
        scene.step()

    # clean up the temporary mesh file
    os.unlink(mesh_path)


if __name__ == "__main__":
    main()
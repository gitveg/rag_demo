import os
import tempfile

import genesis as gs
import trimesh
import numpy as np

# Create a square cloth mesh (1x1 meter, 10x10 subdivision)
def make_square_cloth_mesh(size=1.0, nx=10, ny=10):
    x = np.linspace(-size/2, size/2, nx)
    y = np.linspace(-size/2, size/2, ny)
    vertices = []
    for j in range(ny):
        for i in range(nx):
            vertices.append([x[i], 0.0, y[j]])
    faces = []
    for j in range(ny-1):
        for i in range(nx-1):
            v0 = j*nx + i
            v1 = j*nx + i+1
            v2 = (j+1)*nx + i
            v3 = (j+1)*nx + i+1
            faces.append([v0, v1, v2])
            faces.append([v1, v3, v2])
    return trimesh.Trimesh(vertices=vertices, faces=faces)

# Save mesh to temporary file
mesh = make_square_cloth_mesh()
tmpdir = tempfile.mkdtemp()
mesh_path = os.path.join(tmpdir, "square_cloth.obj")
mesh.export(mesh_path)

# Initialize genesis
gs.init()

# Create scene
scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_fov=30,
        res=(1280, 720),
        max_FPS=60,
    ),
    show_viewer=True,
)

# Add ground plane
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

# Add cloth
cloth = scene.add_entity(
    morph=gs.morphs.Mesh(file=mesh_path),
    material=gs.materials.PBD.Cloth(),
)

# Build the scene
scene.build()

# Run simulation for 1000 steps
for i in range(1000):
    scene.step()
import os
import tempfile

import numpy as np
import trimesh

import genesis as gs

########################## init ##########################
gs.init()

########################## create a scene ##########################
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

########################## helper to create mesh files ##########################

def create_mesh_file(geometry, file_ext=".obj"):
    """Write a trimesh geometry to a temporary file and return its path."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
    path = tmp.name
    tmp.close()
    geometry.export(path)
    return path

# Barrel (cylinder)
barrel_mesh = trimesh.creation.cylinder(radius=0.3, height=0.6, sections=16)
barrel_path = create_mesh_file(barrel_mesh)

# Debris (small spheres)
debris_mesh = trimesh.creation.icosphere(subdivisions=2, radius=0.1)
debris_path = create_mesh_file(debris_mesh)

########################## entities ##########################
# ground
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

# hanging cloth (PBD)
cloth = scene.add_entity(
    morph=gs.morphs.Mesh(
        file="cloth"  # dummy; we will replace with a mesh built from plane
    ),
    material=gs.materials.PBD.Cloth(
        rho=0.5,
        stretch_compliance=1e-7,
        bending_compliance=1e-5,
    ),
)
# Note: The PBD cloth needs a mesh that is a triangulated plane.
# We'll generate a rectangular grid mesh for the cloth.
cloth_mesh = trimesh.creation.box(extents=[2, 0.001, 1.5], subdivisions=[4, 0, 3])
# Actually we want a flat rectangular patch: use a plane with subdivisions.
cloth_mesh = trimesh.creation.box(extents=[2, 0.001, 1.5])  # thin box
# But we need a flat cloth, so use a plane with 4x3 subdivisions.
cloth_mesh = trimesh.creation.box(extents=[2, 0.001, 1.5], subdivisions=[4, 0, 3])
# Better: use a plane created from grid.
cloth_mesh = trimesh.creation.plane(extents=[2, 1.5], subdivisions=4)
cloth_path = create_mesh_file(cloth_mesh, file_ext=".obj")
# Re-add cloth with proper mesh file
scene.remove_entity(cloth)  # remove previous dummy
cloth = scene.add_entity(
    morph=gs.morphs.Mesh(file=cloth_path),
    material=gs.materials.PBD.Cloth(
        rho=0.5,
        stretch_compliance=1e-7,
        bending_compliance=1e-5,
    ),
)

# rigid barrels (multiple)
barrel_positions = [
    (-1.0, 0.3, 0.5),
    (0.0, 0.3, 0.0),
    (1.0, 0.3, -0.5),
]
for pos in barrel_positions:
    scene.add_entity(
        morph=gs.morphs.Mesh(
            file=barrel_path,
            pos=pos,
            euler=(0, 0, np.random.uniform(0, 360)),
            scale=0.5,
        ),
        material=gs.materials.Rigid(rho=500.0, friction=0.8),
    )

# falling debris (small spheres)
for _ in range(20):
    scene.add_entity(
        morph=gs.morphs.Mesh(
            file=debris_path,
            pos=(
                np.random.uniform(-2.0, 2.0),
                np.random.uniform(2.0, 5.0),
                np.random.uniform(-2.0, 2.0),
            ),
        ),
        material=gs.materials.Rigid(rho=200.0, friction=0.3),
    )

########################## force field: strong turbulent wind ##########################
# Add a wind force field (strong, direction roughly along +x)
wind = gs.force_fields.Wind(
    direction=(1.0, 0.2, 0.0),   # wind direction with slight upward component
    strength=50.0,
    radius=5.0,
    center=(0.0, 0.5, 0.0),
)
scene.add_force_field(wind)

########################## build scene ##########################
scene.build()

########################## fix top particles of cloth ##########################
# The cloth mesh is a plane with 4 divisions along width, height.
# Top edge particles: assume index 0,1,2,3,4 (first row)
# In trimesh plane, vertices are ordered row-major.
cloth_entity = scene.entities[-1]  # cloth is last? Actually we don't have easy handle.
# We know cloth was added after barrel and debris? Better to store reference.
# Let's rename cloth entity variable to cloth_entity.
cloth_entity = cloth  # from earlier
# Find top row indices: we have 5 rows x (subdivisions+1) = 5 rows, 5 columns? 4 subdivisions => 5x5 grid.
# Fix the first row (lowest z?) We want top edge in world coordinates. The cloth plane has normal y? We'll fix the row with highest z.
# We'll assume the mesh vertices are in the order: first row (z-min), second row, ... last row (z-max).
# For simplicitly, we can fix vertices with z-coordinate near the top.
verts = cloth_mesh.vertices  # local coordinates, z is up? The plane is in xy plane? Actually trimesh plane is in xy plane, normal z.
# Our cloth morph orientation is default? The plane morph has default orientation? We'll assume the cloth is oriented with normal along +z, so top edge is max y or min y?
# Let's just use the point with maximum y (since extents [2, 1.5], so y from -0.75 to 0.75).
top_mask = verts[:, 1] > 0.7
top_indices = np.where(top_mask)[0]
cloth_entity.set_fixed_particles(top_indices.tolist())

########################## simulation loop ##########################
for i in range(1000):
    scene.step()

########################## cleanup temp files ##########################
# Remove temporary mesh files (optional)
import os
for path in [barrel_path, debris_path, cloth_path]:
    os.remove(path)
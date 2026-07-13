import genesis as gs
import numpy as np

# Initialize Genesis
gs.init()

# Create a scene
scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2, 2, 1.5),
        camera_lookat=(0, 0, 0),
    ),
)

# Parameters for the elastic sheet
width = 1.0          # side length of the square sheet
spacing = 0.05       # vertex spacing in the grid
z_sheet = 0.0        # height of the sheet

# Generate grid vertices for the sheet in the XY plane
x = np.arange(0, width + spacing, spacing)
y = np.arange(0, width + spacing, spacing)
xx, yy = np.meshgrid(x, y)
vertices = np.stack([xx.ravel(), yy.ravel(), np.zeros_like(xx.ravel())], axis=1)

# Shift the sheet so that its center is at (0, 0, z_sheet)
vertices[:, 0] -= width / 2
vertices[:, 1] -= width / 2
vertices[:, 2] = z_sheet

# Build triangular faces
nx = len(x)
ny = len(y)
faces = []
for i in range(nx - 1):
    for j in range(ny - 1):
        # Two triangles per quad
        idx = i * ny + j
        # triangle 1
        faces.append([idx, idx + ny, idx + 1])
        # triangle 2
        faces.append([idx + 1, idx + ny, idx + ny + 1])
faces = np.array(faces, dtype=np.int32)

# Identify boundary vertices (those with x at min/max or y at min/max)
x_vals = vertices[:, 0]
y_vals = vertices[:, 1]
x_min, x_max = x_vals.min(), x_vals.max()
y_min, y_max = y_vals.min(), y_vals.max()
tol = spacing * 0.1
boundary_idx = np.where(
    (np.abs(x_vals - x_min) < tol) |
    (np.abs(x_vals - x_max) < tol) |
    (np.abs(y_vals - y_min) < tol) |
    (np.abs(y_vals - y_max) < tol)
)[0]

# Create the sheet morph with vertices and faces
sheet_morph = gs.morphs.Mesh(v=vertices, f=faces)

# Create the sheet entity (soft elastic sheet)
sheet = scene.add_entity(
    morph=sheet_morph,
    material=gs.materials.FEM(
        young=5e5,       # Young's modulus (Pa)
        poisson=0.4,     # Poisson's ratio
        density=1000,    # density (kg/m^3)
    ),
    surface=gs.surfaces.Default(color=(0.8, 0.2, 0.2, 1.0)),  # reddish
    fix_idx=boundary_idx,   # fix the edges to keep the sheet stretched
)

# Add a rigid sphere above the sheet
ball = scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(0.0, 0.0, 0.3),   # above the sheet center
        radius=0.08,
    ),
    material=gs.materials.Rigid(),
    surface=gs.surfaces.Default(color=(0.2, 0.2, 0.8, 1.0)),  # blue
)

# Build the scene and start the simulation
scene.build()

# Run the simulation loop
while True:
    scene.step()
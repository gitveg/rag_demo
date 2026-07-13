import genesis as gs
import numpy as np

gs.init()

scene = gs.Scene(show_viewer=True)

# create a heightfield for rolling hills
width = 20.0
depth = 20.0
resolution = 0.2

x = np.arange(-width/2, width/2, resolution)
y = np.arange(-depth/2, depth/2, resolution)
X, Y = np.meshgrid(x, y)
Z = 0.5 * np.sin(0.5*X) * np.cos(0.5*Y) + 0.3 * np.sin(1.0*X+1.0) * np.cos(0.8*Y)

# terrain entity
terrain = scene.add_entity(
    gs.morphs.Terrain(
        height_field=Z,
        grid_size=resolution,
        pos=(0, 0, 0),
    ),
    material=gs.materials.Rigid(),
)

# place a box on one of the slopes
# choose a point with nonzero slope
x_box = 5.0
y_box = 0.0
ix = int((x_box + width/2) / resolution)
iy = int((y_box + depth/2) / resolution)
z_box = Z[iy, ix]  # note meshgrid ordering: rows=y, cols=x

box_size = (0.5, 0.5, 0.5)
box = scene.add_entity(
    gs.morphs.Box(
        pos=(x_box, y_box, z_box + box_size[2]/2 + 0.01),
        size=box_size,
    ),
    material=gs.materials.Rigid(),
)

scene.build()

# run simulation
for _ in range(1000):
    scene.step()
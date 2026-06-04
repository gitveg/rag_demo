import genesis as gs
import time

gs.init()

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

# ground plane
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

# rectangular cloth using PBD cloth material and a built-in mesh file
cloth = scene.add_entity(
    morph=gs.morphs.Mesh(file="cloth.obj"),
    material=gs.materials.PBD.Cloth(),
)

scene.build()

# get particle info to set fixed corners
n_vertices = cloth.n_vertices
n_rows = int((n_vertices)**0.5)  # approximate grid size
n_cols = n_vertices // n_rows

# corners: top-left, top-right, bottom-left, bottom-right (assuming grid layout)
corner_indices = [0, n_cols-1, n_vertices-n_cols, n_vertices-1]
# fix all four corners
cloth.set_fixed_vertices(corner_indices, True)

# initial sag under gravity for 2 seconds (500 steps at dt 4e-3 * substeps? The step() advances one dt)
# This loop runs the viewer automatically.
for i in range(500):
    scene.step()
    time.sleep(0.01)

# release the two right corners (indices 1 and 3 in corner list)
release_indices = [corner_indices[1], corner_indices[3]]
cloth.set_fixed_vertices(release_indices, False)

# continue simulation to watch cloth swing
for i in range(1000):
    scene.step()
    time.sleep(0.01)
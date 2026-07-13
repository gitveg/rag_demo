import genesis as gs

gs.init()

scene = gs.Scene(
    gravity=(0, 0, -9.81),
    viewer_options=gs.options.ViewerOptions(show_fps=True),
)

# Ground plane to catch falling objects
ground = scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Static(),
)

# Table box
table = scene.add_entity(
    morph=gs.morphs.Box(size=(1.0, 1.0, 0.5)),
    material=gs.materials.Static(),
    pos=(0, 0, 0.25),   # center at z=0.25, top at z=0.5
)

# Tablecloth mesh
cloth = scene.add_entity(
    morph=gs.morphs.Mesh(
        file="meshes/cloth.obj",
        scale=(1.2, 1.2, 1.0),
        pos=(0, 0, 0.6),  # slightly above table
    ),
    material=gs.materials.PBDCloth(),
    surface=gs.surfaces.Default(color=(1.0, 0.8, 0.6)),
)

# Rigid cubes to drop
cube_size = 0.05
for i in range(5):
    x = (i - 2) * 0.2
    y = 0
    z = 0.8
    cube = scene.add_entity(
        morph=gs.morphs.Box(size=(cube_size, cube_size, cube_size)),
        material=gs.materials.Rigid(density=1000),
        surface=gs.surfaces.Default(color=(0.2, 0.6, 0.8)),
        pos=(x, y, z),
    )

scene.build()
scene.start_viewer()

# Simulate for a few seconds
for _ in range(2000):
    scene.step()

# The viewer will remain open until the script ends.
# To keep the window open after simulation, you may add a blocking call depending on your version,
# e.g., scene.viewer.wait_close() — omitted here to keep the script minimal and non‑blocking.
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=4e-3, substeps=10),
    viewer_options=gs.options.ViewerOptions(
        camera_fov=30,
        res=(1280, 720),
        max_FPS=60,
    ),
    show_viewer=True,
)

plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

cloth = scene.add_entity(
    morph=gs.morphs.Mesh(file='cloth.obj', scale=(2, 1, 1), pos=(0, 2, 0)),
    material=gs.materials.PBD.Cloth(),
)

scene.build()

# Fix the two top corners of the cloth (assume vertex indices 0 and 1)
cloth.set_fixed_particles([0, 1])

wind = gs.force_fields.Wind(
    direction=(1, 0, 0),
    strength=0.5,
    radius=2,
    center=(0, 2, 0)
)
scene.add_force_field(wind)

for i in range(1000):
    scene.step()
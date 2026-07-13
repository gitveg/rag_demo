import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    show_viewer=True,
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3, -3, 2),
        camera_lookat=(0, 0, 0.5),
        camera_fov=30,
    ),
    gravity=(0, 0, -9.81),
)

# floor
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
    surface=gs.surfaces.Default(),
)

# soft elastic beam (cantilever)
fem_beam = gs.materials.FEM(
    youngs_modulus=5e6,
    poisson_ratio=0.3,
    density=1000,
)
beam = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0, 0, 1.0),
        size=(2.0, 0.1, 0.1),
    ),
    material=fem_beam,
    surface=gs.surfaces.Soft(),
)

# soft elastic sphere
fem_sphere = gs.materials.FEM(
    youngs_modulus=1e5,
    poisson_ratio=0.3,
    density=500,
)
sphere = scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(1.0, 0, 1.5),
        radius=0.3,
    ),
    material=fem_sphere,
    surface=gs.surfaces.Soft(),
)

scene.build()

# fix the beam at its left end (nodes with x < -0.9)
fixed_mask = beam.verts[:, 0] < -0.9
beam.set_fixed_verts(fixed_mask)

# simulate
for i in range(500):
    scene.step()
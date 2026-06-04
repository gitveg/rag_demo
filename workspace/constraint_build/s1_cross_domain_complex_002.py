import genesis as gs

gs.init()

# Create scene with PBD and MPM solvers enabled
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
    pbd_options=gs.options.PBDOptions(),
    mpm_options=gs.options.MPMOptions(),
    show_viewer=True,
)

# Add ground plane
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

# Add a cloth sheet (curtain mesh rotated to lie flat)
cloth = scene.add_entity(
    morph=gs.morphs.Mesh(
        file="meshes/curtain/curtain.obj",
        pos=(0.0, 0.3, 0.0),
        euler=(90.0, 0.0, 0.0),  # rotate to horizontal
        scale=1.0,
    ),
    material=gs.materials.PBD.Cloth(),
    surface=gs.surfaces.Default(),
)

# Add a sand emitter above the cloth
emitter = scene.add_emitter(
    material=gs.materials.MPM.Sand(),
    max_particles=50000,
    surface=gs.surfaces.Default(),
)

# Build the scene
scene.build()

# Simulation loop
for i in range(1000):
    scene.step()
import genesis as gs

# Initialize Genesis
gs.init(backend=gs.gpu)

# Create the scene
scene = gs.Scene(
    renderer=gs.renderers.Rasterizer,
    show_viewer=False
)

# Add a camera to observe the scene
camera = scene.add_camera(
    res=(1280, 720),
    pos=(1.5, 0.8, 1.5),
    lookat=(0.0, 0.15, 0.0),
    fov=30,
)

# Add a directional light
scene.add_light(
    ambient=(0.3, 0.3, 0.3),
    diffuse=(0.8, 0.8, 0.8),
    specular=(1.0, 1.0, 1.0),
)

# Create the transparent cubical tank (half-open top)
tank = scene.add_entity(
    morph=gs.morphs.Box(
        lower=(-0.5, -0.5, 0.0),
        upper=(0.5, 0.5, 0.5),
    ),
    surface=gs.surfaces.Glass(
        color=(0.8, 0.8, 0.8, 0.3),  # semi-transparent
    ),
)

# Define a liquid material
liquid_material = scene.add_material(
    gs.materials.Liquid(
        particle_radius=0.01,
        density=1000.0,
        viscosity=0.001,
    )
)

# Fill the tank halfway with liquid particles
# The tank inner volume: [-0.5,0.5] in X/Y, and height [0,0.5].
# Half-fill means from z=0 to z=0.25.
fluid_source = scene.add_entity(
    material=liquid_material,
    morph=gs.morphs.Box(
        lower=(-0.45, -0.45, 0.01),
        upper=(0.45, 0.45, 0.24),
    ),
    is_source=True,
)

# Build the scene (populate particles, etc.)
scene.build()

# Run simulation steps to let fluid settle
for _ in range(300):
    scene.step()

# Optional: render the final frame
# scene.render()  # uncomment if needed for saving an image

# Keep viewer open to observe the result (if show_viewer=True)
# if scene.show_viewer:
#    scene.viewer.wait()

# Cleanup
gs.exit()
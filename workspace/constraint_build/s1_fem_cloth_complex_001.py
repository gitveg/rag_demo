import genesis as gs

# Initialize genesis
gs.init()

# Create a scene
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

# Add a ground plane
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
)

# Create a cloth curtain (thin box) hanging from the top edge
# The box is 1.0 wide, 1.0 tall, and thin (0.01)
curtain = scene.add_entity(
    morph=gs.morphs.Box(
        size=(1.0, 1.0, 0.01),
        pos=(0.0, 0.5, 0.0),  # bottom at y=0, top at y=1.0
    ),
    material=gs.materials.PBD.Cloth(),
    # Fix the top face vertices (indices: 0,1,2,3 for a box)
    fixed_particles=[0, 1, 2, 3],
)

# Add a rigid sphere (radius 0.1)
sphere = scene.add_entity(
    morph=gs.morphs.Sphere(
        radius=0.1,
        pos=(-1.0, 0.5, 0.0),  # start left of curtain
    ),
    material=gs.materials.Rigid(),
)

# Build the scene
scene.build()

# Set the sphere's velocity to throw it horizontally into the curtain
sphere.set_velocity([3.0, 0.0, 0.0])  # moving right

# Run simulation for a few seconds
# (This loop runs in the viewer, so we just step indefinitely)
# The viewer will handle the rendering.
for i in range(2000):
    scene.step()
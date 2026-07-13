import genesis as gs

gs.init()

# Create scene
scene = gs.Scene(
    gravity=(0.0, 0.0, -9.81),
)

# Ground (thin box)
ground = scene.add_entity(
    gs.morphs.Box(size=(2.2, 2.2, 0.1)),
    position=(0.0, 0.0, -0.05),
    fixed=True,
)

# Walls (four boxes)
wall_thickness = 0.1
wall_height = 0.5
inner_half = 1.0

# Left wall
left_wall = scene.add_entity(
    gs.morphs.Box(size=(wall_thickness, 2.2, wall_height)),
    position=(-inner_half, 0.0, wall_height / 2),
    fixed=True,
)

# Right wall
right_wall = scene.add_entity(
    gs.morphs.Box(size=(wall_thickness, 2.2, wall_height)),
    position=(inner_half, 0.0, wall_height / 2),
    fixed=True,
)

# Back wall
back_wall = scene.add_entity(
    gs.morphs.Box(size=(2.2, wall_thickness, wall_height)),
    position=(0.0, -inner_half, wall_height / 2),
    fixed=True,
)

# Front wall
front_wall = scene.add_entity(
    gs.morphs.Box(size=(2.2, wall_thickness, wall_height)),
    position=(0.0, inner_half, wall_height / 2),
    fixed=True,
)

# Ball
ball = scene.add_entity(
    gs.morphs.Sphere(radius=0.15),
    position=(0.5, 0.0, 0.3),   # off-center, slightly above ground
    mass=1.0,
    material=gs.materials.Rigid(),
)

# Build the scene
scene.build()

# Viewer (optional)
scene.viewer = gs.viewer.Viewer()

# Simulation loop
force_magnitude = 0.5  # tangential force strength

for step in range(1000):
    # Compute position of the ball relative to center
    pos = ball.get_position()
    rx, ry = pos[0], pos[1]

    # Tangential direction: rotate radial vector by 90 degrees CCW
    fx = -ry
    fy =  rx
    norm = (fx**2 + fy**2) ** 0.5
    if norm > 1e-6:
        fx *= force_magnitude / norm
        fy *= force_magnitude / norm

    # Apply rotating force in the horizontal plane
    ball.add_force((fx, fy, 0.0))

    scene.step()

# Clean up
scene.viewer.close()
gs.exit()
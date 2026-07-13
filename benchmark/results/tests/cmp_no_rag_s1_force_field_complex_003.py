import genesis as gs

gs.init()

# Create a scene with default options
scene = gs.Scene()

# Add a central point represented by a small static sphere
center = scene.add_entity(
    gs.morphs.Sphere(radius=0.1),
    material=gs.materials.Rigid(fixed=True),
    pos=(0, 0, 0),
)

# Add several dynamic objects around the center
objects = []
positions = [(2, 0, 0), (-2, 0, 0), (0, 2, 0), (0, -2, 0), (1.5, 1.5, 0)]
for pos in positions:
    obj = scene.add_entity(
        gs.morphs.Sphere(radius=0.2),
        material=gs.materials.Rigid(),
        pos=pos,
    )
    objects.append(obj)

# Build the scene (required after adding entities)
scene.build()

force_magnitude = 200.0

# Simulation loop
for i in range(300):
    for obj in objects:
        # Vector from object to center
        direction = center.get_pos() - obj.get_pos()
        dist_sq = direction[0]**2 + direction[1]**2 + direction[2]**2
        if dist_sq > 1e-6:
            direction_normalized = direction / (dist_sq ** 0.5)
        else:
            direction_normalized = gs.Vector3(0, 0, 0)
        # Apply radial force toward the center
        force = direction_normalized * force_magnitude
        obj.force.set_world_force(force)
    scene.step()
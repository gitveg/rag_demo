import genesis as gs

gs.init()

scene = gs.Scene(
    gravity=(0, 0, -9.81),
    show_viewer=True,
)

# Create a gently sloped terrain
terrain = scene.add_entity(
    gs.morphs.Terrain(subterrain_types="sloped_terrain"),
)

# Place a rigid sphere on the slope
ball = scene.add_entity(
    gs.morphs.Sphere(radius=0.3),
    material=gs.materials.Rigid(),
    pos=(0, 0, 3.0),   # start above the slope
)

scene.build()

# Run simulation so the ball rolls downhill
for _ in range(1000):
    scene.step()
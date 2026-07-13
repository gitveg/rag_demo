import genesis as gs

gs.init()

scene = gs.Scene()

tile_size = 1.0

# Create 3x3 terrain grid with half sloped and half stairs
for i in range(3):
    for j in range(3):
        if (i + j) % 2 == 0:
            ttype = 'sloped_terrain'
        else:
            ttype = 'stairs_terrain'
        x = (i - 1) * tile_size
        y = (j - 1) * tile_size
        scene.add_entity(
            gs.morphs.Terrain(type=ttype),
            position=(x, y, 0.0)
        )

# Place a rigid box on a sloped tile
box_i, box_j = 0, 0  # sloped tile
box_x = (box_i - 1) * tile_size
box_y = (box_j - 1) * tile_size
box = scene.add_entity(
    gs.morphs.Box(size=(0.2, 0.2, 0.2), fixed=False),
    position=(box_x, box_y, 1.5)  # initial height above slope
)

# Place a sphere on a stairs tile
sphere_i, sphere_j = 0, 1  # stairs tile
sphere_x = (sphere_i - 1) * tile_size
sphere_y = (sphere_j - 1) * tile_size
sphere = scene.add_entity(
    gs.morphs.Sphere(radius=0.1, fixed=False),
    position=(sphere_x, sphere_y, 1.5)  # initial height above stairs
)

scene.build()

# Simulate for a while to observe sliding/rolling
for step in range(500):
    scene.step()
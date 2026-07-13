import genesis as gs

gs.init()

scene = gs.Scene()

# Ground plane
plane = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(fixed=True),
)

# Three squishy spheres in a row
radii = [0.2, 0.3, 0.15]
x_positions = [-0.6, 0.0, 0.6]
drop_height = 1.0

for r, x in zip(radii, x_positions):
    scene.add_entity(
        gs.morphs.Sphere(radius=r, pos=(x, 0.0, drop_height)),
        material=gs.materials.FEM(),   # elastic, deformable
    )

scene.build()

# Run simulation for a few seconds
for _ in range(300):
    scene.step()
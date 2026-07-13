import genesis as gs

gs.init()

scene = gs.Scene(
    show_viewer=True,
)

sphere = scene.add_entity(
    gs.morphs.Sphere(radius=0.2),
    material=gs.materials.Rigid(),
    pos=(0, 0, 2),
)

plane = scene.add_entity(
    gs.morphs.Plane(),
)

scene.build()

wind_force = (5.0, 0.0, 0.0)

for _ in range(500):
    sphere.add_force(force=wind_force)
    scene.step()
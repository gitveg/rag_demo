import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    show_viewer=True,
)

plane = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(),
)

ball = scene.add_entity(
    gs.morphs.Sphere(radius=0.3, pos=(0.0, 0.0, 2.0)),
    material=gs.materials.Rigid(),
    surface=gs.surfaces.Default(color=(1.0, 0.0, 0.0)),
)

scene.build()

for _ in range(400):
    scene.step()
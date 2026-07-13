import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(),
    surface=gs.surfaces.Rough(color=(0.5, 0.5, 0.5)),
)

sphere = scene.add_entity(
    gs.morphs.Sphere(pos=(0.0, 0.0, 0.5), radius=0.5),
    material=gs.materials.Rigid(),
    surface=gs.surfaces.Metal(color=(1.0, 0.0, 0.0), roughness=0.1),
)

box = scene.add_entity(
    gs.morphs.Box(pos=(1.5, 0.0, 0.5), size=(1.0, 1.0, 1.0)),
    material=gs.materials.Rigid(),
    surface=gs.surfaces.Rough(color=(1.0, 1.0, 0.0), roughness=0.8),
)

scene.build()

for _ in range(100):
    scene.step()
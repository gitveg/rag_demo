import genesis as gs

gs.init()

scene = gs.Scene(show_viewer=True)

plane = scene.add_entity(gs.morphs.Plane())

sphere = scene.add_entity(
    gs.morphs.Sphere(pos=(0, 0.5, 0), radius=0.5),
    material=gs.materials.Rigid(),
    surface=gs.surfaces.Metallic(color=(0.9, 0.9, 0.9)),
)

scene.build()

gs.simulate(scene)
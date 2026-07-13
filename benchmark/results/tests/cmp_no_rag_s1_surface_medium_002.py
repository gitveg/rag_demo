import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(),
    vis_options=gs.options.VisOptions(),
)

# Matte red plastic cube
cube1 = scene.add_entity(
    gs.morphs.Box(pos=(-1.5, 0.0, 0.5), size=(1.0, 1.0, 1.0)),
    material=gs.materials.Rigid(),
    color=(0.8, 0.1, 0.1),
)

# Rough concrete cube
cube2 = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 0.5), size=(1.0, 1.0, 1.0)),
    material=gs.materials.Rigid(),
    color=(0.55, 0.55, 0.55),
)

# Polished gold metal cube
cube3 = scene.add_entity(
    gs.morphs.Box(pos=(1.5, 0.0, 0.5), size=(1.0, 1.0, 1.0)),
    material=gs.materials.Rigid(),
    color=(1.0, 0.84, 0.0),
)

# Ground plane
scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(),
)

scene.build()

for _ in range(1000):
    scene.step()
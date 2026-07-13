import genesis as gs

gs.init()

scene = gs.Scene()

# Large static rigid box at origin
scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 0.0), size=(2.0, 2.0, 0.1)),
    rigid=True,
    static=True,
)

# Small rigid sphere falling directly onto the center of the box
scene.add_entity(
    gs.morphs.Sphere(pos=(0.0, 0.0, 0.5), radius=0.05),
    rigid=True,
)

scene.build()

for _ in range(1000):
    scene.step()
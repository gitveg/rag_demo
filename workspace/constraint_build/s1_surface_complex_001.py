import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene()

plane = scene.add_entity(
    gs.morphs.Plane(),
)

franka = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
    surface=gs.surfaces.PolishedMetal(),  # hypothetical, but we need something
)

# Place a translucent red box in front of the robot
# Using Box morph (assuming it exists) with a semi-transparent red color and rough surface
box = scene.add_entity(
    gs.morphs.Box(size=(0.2, 0.2, 0.2), pos=(0.5, 0.0, 0.1)),
    surface=gs.surfaces.TranslucentRedRough(),
)

scene.build()

for i in range(1000):
    scene.step()
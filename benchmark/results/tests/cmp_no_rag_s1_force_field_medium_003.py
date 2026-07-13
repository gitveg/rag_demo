import genesis as gs
import random

gs.init()

# Wind force: horizontal push
wind = gs.options.Wind(direction=(1.0, 0.0, 0.0), amplitude=50.0)
sim_options = gs.options.SimOptions(wind=wind)

scene = gs.Scene(sim_options=sim_options)

# Ground plane
plane = scene.add_entity(gs.morpho.Plane())

# Small light cubes scattered on the floor
box_morph = gs.morpho.Box(size=(0.1, 0.1, 0.1), mass=0.01)

for _ in range(20):
    x = random.uniform(-3.0, 3.0)
    z = random.uniform(-3.0, 3.0)
    cube = scene.add_entity(box_morph, pos=(x, 0.2, z))

scene.build()

for _ in range(1000):
    scene.step()
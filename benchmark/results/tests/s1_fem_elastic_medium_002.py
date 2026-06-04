"""
User Query: Place two soft elastic cubes with different stiffness values above the floor and let them fall at the same time to compare how much they deform after impact.
task_id: s1_fem_elastic_medium_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.005),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(
        rho=200.0,
        friction=1.0,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

soft_cube_stiff = scene.add_entity(
    gs.morphs.Box(pos=(-0.35, 0.0, 0.9), size=(0.3, 0.3, 0.3)),
    material=gs.materials.FEM.Elastic(
        rho=1000.0,
        E=2.0e5,
        nu=0.2,
        model="linear",
    ),
    surface=gs.surfaces.Default(color=(0.2, 0.4, 1.0, 1.0)),
)

soft_cube_soft = scene.add_entity(
    gs.morphs.Box(pos=(0.35, 0.0, 0.9), size=(0.3, 0.3, 0.3)),
    material=gs.materials.FEM.Elastic(
        rho=1000.0,
        E=3.0e4,
        nu=0.2,
        model="linear",
    ),
    surface=gs.surfaces.Default(color=(1.0, 0.4, 0.2, 1.0)),
)

scene.build()

for i in range(800):
    scene.step()
    if i % 100 == 0:
        print(f"step={i}")

print("Simulation complete.")
print("Blue cube: stiffer elastic material, expected to deform less after impact.")
print("Orange cube: softer elastic material, expected to deform more after impact.")
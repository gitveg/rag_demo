"""
User Query: Simulate a large tablecloth being dropped onto a round dining table. Ensure the cloth is large enough to create realistic folds and overhangs around the table edges.
task_id: s1_fem_cloth_complex_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.005),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Rough(color=(0.85, 0.85, 0.85, 1.0)),
)

table_material = gs.materials.Rigid(rho=600.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0)
table_surface = gs.surfaces.Default(color=(0.45, 0.28, 0.18, 1.0))

scene.add_entity(
    gs.morphs.Cylinder(
        pos=(0.0, 0.0, 0.76),
        radius=0.6,
        height=0.06,
    ),
    material=table_material,
    surface=table_surface,
)

scene.add_entity(
    gs.morphs.Cylinder(
        pos=(0.0, 0.0, 0.39),
        radius=0.08,
        height=0.74,
    ),
    material=table_material,
    surface=table_surface,
)

scene.add_entity(
    gs.morphs.Cylinder(
        pos=(0.0, 0.0, 0.02),
        radius=0.35,
        height=0.04,
    ),
    material=table_material,
    surface=table_surface,
)

scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 1.25),
        size=(1.8, 1.8, 0.02),
    ),
    material=gs.materials.FEM.Cloth(
        rho=0.5,
        E=3.0e4,
        nu=0.49,
        thickness=0.003,
        model="stable_neohookean",
    ),
    surface=gs.surfaces.Default(color=(0.95, 0.95, 0.98, 1.0)),
)

scene.build()

for _ in range(1200):
    scene.step()
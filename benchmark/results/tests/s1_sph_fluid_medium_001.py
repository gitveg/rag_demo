"""
User Query: Simulate a stream of water pouring from above onto a slanted surface, letting it flow down and pool at the bottom.
task_id: s1_sph_fluid_medium_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=8,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.9, restitution=0.05),
    surface=gs.surfaces.Rough(color=(0.45, 0.45, 0.45, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.9),
        size=(3.0, 1.2, 0.12),
        euler=(0.0, -25.0, 0.0),
    ),
    material=gs.materials.Rigid(rho=1200, friction=0.4, restitution=0.02),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(1.25, 0.0, 0.18),
        size=(0.25, 1.6, 0.35),
    ),
    material=gs.materials.Rigid(rho=1200, friction=0.7, restitution=0.02),
    surface=gs.surfaces.Rough(color=(0.35, 0.35, 0.38, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(1.95, 0.0, 0.12),
        size=(1.2, 1.8, 0.24),
    ),
    material=gs.materials.Rigid(rho=1200, friction=0.8, restitution=0.02),
    surface=gs.surfaces.Rough(color=(0.3, 0.3, 0.34, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-0.85, 0.0, 1.8),
        size=(0.22, 0.22, 1.0),
    ),
    material=gs.materials.SPH.Liquid(sampler="regular"),
    surface=gs.surfaces.Glass(color=(0.4, 0.7, 1.0, 0.5)),
)

scene.add_camera(
    pos=(5.0, -4.5, 3.0),
    lookat=(0.7, 0.0, 0.7),
    res=(1280, 720),
)

scene.build()

for _ in range(1200):
    scene.step()
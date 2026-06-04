"""
User Query: Release a pile of dry sand above the ground and let it form a natural cone-shaped heap.
task_id: s1_mpm_sand_simple_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=10,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, -3.5, 2.2),
        camera_lookat=(0.0, 0.0, 0.5),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(
        rho=1000,
        friction=0.9,
        restitution=0.05,
    ),
    surface=gs.surfaces.Rough(color=(0.75, 0.75, 0.75, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Cylinder(
        pos=(0.0, 0.0, 0.9),
        radius=0.25,
        height=0.6,
    ),
    material=gs.materials.MPM.Sand(
        sampler="regular",
    ),
    surface=gs.surfaces.Rough(color=(0.82, 0.72, 0.48, 1.0)),
)

scene.build()

for _ in range(800):
    scene.step()
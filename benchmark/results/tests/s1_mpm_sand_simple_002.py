"""
User Query: A column of dry sand particles drops onto the floor and forms a small mound.
task_id: s1_mpm_sand_simple_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=10,
        gravity=(0.0, 0.0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.5, -2.0, 1.8),
        camera_lookat=(0.0, 0.0, 0.4),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(
        rho=2000,
        friction=0.9,
        restitution=0.05,
    ),
    surface=gs.surfaces.Rough(color=(0.75, 0.75, 0.78, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Cylinder(
        pos=(0.0, 0.0, 0.8),
        radius=0.12,
        height=0.5,
    ),
    material=gs.materials.MPM.Sand(
        sampler="regular",
    ),
    surface=gs.surfaces.Rough(color=(0.85, 0.72, 0.45, 1.0)),
)

scene.build()

for _ in range(600):
    scene.step()
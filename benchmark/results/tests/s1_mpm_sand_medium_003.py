"""
User Query: Release two blocks of sand from different heights so they collide and merge into a single pile on the ground.
task_id: s1_mpm_sand_medium_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=10,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(4.5, -3.5, 2.8),
        camera_lookat=(0.0, 0.0, 0.7),
        camera_fov=45,
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
    surface=gs.surfaces.Rough(color=(0.45, 0.45, 0.45, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(-0.35, 0.0, 1.4),
        size=(0.45, 0.45, 0.45),
    ),
    material=gs.materials.MPM.Sand(
        sampler="regular",
    ),
    surface=gs.surfaces.Rough(color=(0.85, 0.72, 0.45, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0.35, 0.0, 2.2),
        size=(0.45, 0.45, 0.45),
    ),
    material=gs.materials.MPM.Sand(
        sampler="regular",
    ),
    surface=gs.surfaces.Rough(color=(0.92, 0.80, 0.52, 1.0)),
)

scene.build()

for _ in range(700):
    scene.step()
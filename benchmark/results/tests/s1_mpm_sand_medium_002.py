"""
User Query: Drop a rigid sphere onto a flat layer of sand and simulate the sand scattering and forming a crater.
task_id: s1_mpm_sand_medium_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.005),
    mpm_options=gs.options.MPMOptions(),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3.0, -3.0, 2.2),
        camera_lookat=(0.0, 0.0, 0.4),
    ),
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
    surface=gs.surfaces.Default(color=(0.7, 0.7, 0.72, 1.0)),
)

scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 0.12),
        size=(1.2, 1.2, 0.24),
    ),
    material=gs.materials.MPM.Sand(sampler="regular"),
    surface=gs.surfaces.Rough(color=(0.76, 0.68, 0.45, 1.0)),
)

scene.add_entity(
    gs.morphs.Sphere(
        pos=(0.0, 0.0, 0.9),
        radius=0.12,
    ),
    material=gs.materials.Rigid(
        rho=800.0,
        friction=0.6,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

cam = scene.add_camera(
    res=(1280, 720),
    pos=(3.0, -3.0, 2.2),
    lookat=(0.0, 0.0, 0.35),
    fov=50,
)

scene.start_recording()
scene.build()

for i in range(500):
    scene.step()
    if i % 2 == 0:
        cam.render()

scene.stop_recording(save_to_filename="s1_mpm_sand_medium_002.mp4")
"""
User Query: Import a terrain mesh (use gs.morphs.Mesh(file="meshes/terrain_45.obj")) as a rigid surface. Simulate a rigid ball rolling from the peak down into the crevices of the mesh terrain.
task_id: s1_terrain_complex_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.Rasterizer(),
)

terrain = scene.add_entity(
    morph=gs.morphs.Mesh(
        file="meshes/terrain_45.obj",
        pos=(0.0, 0.0, 0.0),
        scale=1.0,
        fixed=True,
    ),
    material=gs.materials.Rigid(
        rho=200.0,
        friction=1.2,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Rough(color=(0.45, 0.42, 0.38, 1.0)),
)

ball = scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(0.0, 0.0, 2.0),
        radius=0.18,
    ),
    material=gs.materials.Rigid(
        rho=500.0,
        friction=0.6,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

cam = scene.add_camera(
    pos=(6.0, -6.0, 4.5),
    lookat=(0.0, 0.0, 1.0),
    res=(1280, 720),
    fov=50,
)

scene.build()

for i in range(1200):
    scene.step()
    if i % 60 == 0:
        pos = ball.get_pos()
        print(f"step={i:04d}, ball_pos=({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
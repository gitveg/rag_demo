"""
User Query: Create a scene with two moving rigid cubes and place one camera above the scene and another at ground level to record the motion from different perspectives.
task_id: s1_camera_medium_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    renderer=gs.options.renderers.Rasterizer(),
)

ground = scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.2),
    surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
)

cube_1 = scene.add_entity(
    morph=gs.morphs.Box(pos=(-1.0, 0.0, 0.5), size=(0.5, 0.5, 0.5)),
    material=gs.materials.Rigid(rho=500, friction=0.5, restitution=0.3),
    surface=gs.surfaces.Default(color=(1.0, 0.2, 0.2, 1.0)),
)

cube_2 = scene.add_entity(
    morph=gs.morphs.Box(pos=(1.0, 0.0, 0.5), size=(0.5, 0.5, 0.5)),
    material=gs.materials.Rigid(rho=500, friction=0.5, restitution=0.3),
    surface=gs.surfaces.Default(color=(0.2, 0.2, 1.0, 1.0)),
)

cam_top = scene.add_camera(
    pos=(0.0, 0.0, 6.0),
    lookat=(0.0, 0.0, 0.0),
    res=(640, 480),
)

cam_ground = scene.add_camera(
    pos=(0.0, -6.0, 1.2),
    lookat=(0.0, 0.0, 0.5),
    res=(640, 480),
)

scene.start_recording()
scene.build()

cube_1.set_velocity((1.0, 0.6, 0.0))
cube_2.set_velocity((-1.0, -0.4, 0.0))

for i in range(240):
    scene.step()
    cam_top.render()
    cam_ground.render()

scene.stop_recording()
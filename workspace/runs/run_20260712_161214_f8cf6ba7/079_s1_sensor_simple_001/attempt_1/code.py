import genesis as gs
import numpy as np

gs.init(backend=gs.gpu)

scene = gs.Scene(
    rigid_options=gs.options.RigidOptions(),
    show_viewer=False,
)

plane = scene.add_entity(gs.morphs.Plane())

sphere = scene.add_entity(
    morph=gs.morphs.Sphere(pos=(0.0, 0.0, 0.1), radius=0.1),
)

camera = scene.add_camera(
    res=(320, 240),
    pos=(0.0, 0.0, 0.5),
    lookat=(0.0, 0.0, 0.0),
    fov=40,
    env_idx=0,
)

scene.build()

for _ in range(60):
    scene.step()

result = camera.render()
depth = result['depth']

print("Depth map shape:", depth.shape)
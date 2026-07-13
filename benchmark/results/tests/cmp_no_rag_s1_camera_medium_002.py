import genesis as gs
import numpy as np
import cv2
import os

gs.init()

scene = gs.Scene()

# Ground plane
plane = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(),
)

# Two cubes that will move
cube1 = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 1.0), size=(0.5, 0.5, 0.5)),
    material=gs.materials.Rigid(),
)
cube2 = scene.add_entity(
    gs.morphs.Box(pos=(1.0, 0.0, 1.0), size=(0.5, 0.5, 0.5)),
    material=gs.materials.Rigid(),
)

# Give them initial horizontal velocities
cube1.set_velocity(lin_vel=(1.0, 0.0, 0.0))
cube2.set_velocity(lin_vel=(-1.0, 0.0, 0.0))

# Cameras: one above, one at ground level
cam_above = scene.add_camera(
    res=(640, 480),
    pos=(0.0, 0.0, 10.0),
    lookat=(0.0, 0.0, 0.0),
    fov=60,
)

cam_ground = scene.add_camera(
    res=(640, 480),
    pos=(5.0, 0.0, 1.0),
    lookat=(0.0, 0.0, 0.5),
    fov=60,
)

# Build the scene
scene.build()

# Prepare output folders
os.makedirs("above", exist_ok=True)
os.makedirs("ground", exist_ok=True)

# Simulation loop
for i in range(100):
    scene.step()

    # Render from both cameras
    img_above = cam_above.render(rgb=True, depth=False)
    img_ground = cam_ground.render(rgb=True, depth=False)

    # Convert to BGR uint8 for OpenCV saving
    img_above_bgr = cv2.cvtColor((img_above * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    img_ground_bgr = cv2.cvtColor((img_ground * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)

    cv2.imwrite(f"above/frame_{i:04d}.png", img_above_bgr)
    cv2.imwrite(f"ground/frame_{i:04d}.png", img_ground_bgr)
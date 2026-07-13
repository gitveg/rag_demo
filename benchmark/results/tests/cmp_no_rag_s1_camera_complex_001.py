import genesis as gs
import numpy as np

gs.init()

# Create scene without viewer (headless recording)
scene = gs.Scene(
    show_viewer=False,
)

# Static tilted box as the slope
slope = scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 0.0),
        size=(5.0, 0.2, 2.0),
        euler=(30.0, 0.0, 0.0),  # pitched 30° around x-axis
    ),
    fixed=True,
)

# Rigid box placed near the top of the slope
box = scene.add_entity(
    gs.morphs.Box(
        pos=(2.5, 0.0, 0.2),  # top end, slightly above surface
        size=(0.4, 0.4, 0.4),
    ),
)

scene.build()

# Add two cameras for recording
cam_side = scene.add_camera(res=(640, 480))
cam_side.start_recording("side_view.mp4")

cam_top = scene.add_camera(res=(640, 480))
cam_top.start_recording("top_view.mp4")

# Simulation loop
for _ in range(500):
    box_pos = box.get_pos()

    # Side camera: positioned to the side and slightly above the box
    cam_side.set_pose(
        pos=box_pos + np.array([3.0, 0.5, 1.5]),
        lookat=box_pos,
    )

    # Top camera: directly above the box
    cam_top.set_pose(
        pos=box_pos + np.array([0.0, 0.0, 4.0]),
        lookat=box_pos,
    )

    scene.step()

# Finalize recordings
cam_side.stop_recording()
cam_top.stop_recording()

gs.close()
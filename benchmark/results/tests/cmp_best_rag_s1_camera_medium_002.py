import os
import numpy as np

import genesis as gs
from genesis.utils.misc import tensor_to_array


def main():
    # Initialize Genesis
    gs.init(backend=gs.gpu)

    # Create scene (no viewer to avoid overhead during rendering)
    scene = gs.Scene(show_viewer=False)

    # Ground plane
    scene.add_entity(gs.morphs.Plane())

    # Two rigid cubes that will fall and interact
    cube1 = scene.add_entity(
        gs.morphs.Box(pos=(0.0, 0.0, 1.5), size=(0.2, 0.2, 0.2))
    )
    cube2 = scene.add_entity(
        gs.morphs.Box(pos=(0.5, 0.0, 1.8), size=(0.2, 0.2, 0.2))
    )

    # Camera 1: top-down view (above the scene)
    cam_top = scene.add_camera(
        pos=(0.0, 0.0, 5.0),
        lookat=(0.0, 0.0, 1.0),
        up=(0.0, 1.0, 0.0),   # ensure y is up for top view
        fov=40,
        res=(320, 240),
    )

    # Camera 2: ground-level side view
    cam_side = scene.add_camera(
        pos=(3.0, 0.0, 1.0),
        lookat=(0.2, 0.0, 1.0),
        fov=40,
        res=(320, 240),
    )

    # Build the scene (mandatory before stepping)
    scene.build()

    # Directories for recorded frames
    os.makedirs("top_frames", exist_ok=True)
    os.makedirs("side_frames", exist_ok=True)

    # Simulation loop: record frames every 5 steps
    for i in range(300):
        scene.step()

        if i % 5 == 0:
            # Capture RGB images from both cameras
            rgb_top = tensor_to_array(cam_top.rgb())
            rgb_side = tensor_to_array(cam_side.rgb())

            # Save as PNG files
            filename_top = f"top_frames/frame_{i:04d}.png"
            filename_side = f"side_frames/frame_{i:04d}.png"

            # Use matplotlib to save (requires matplotlib, but already likely available)
            import matplotlib.pyplot as plt
            plt.imsave(filename_top, rgb_top)
            plt.imsave(filename_side, rgb_side)

    print("Recording complete. Frames saved in top_frames/ and side_frames/.")


if __name__ == "__main__":
    main()
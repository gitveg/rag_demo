import time
import os
import numpy as np
import genesis as gs

def main():
    gs.init(backend=gs.cpu)

    viewer_options = gs.options.ViewerOptions(
        camera_pos=(5.0, -5.0, 2.5),
        camera_lookat=(0.0, 0.0, 0.0),
        camera_fov=40,
        max_FPS=200,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        show_viewer=True,
    )

    # Ground plane
    plane = scene.add_entity(morph=gs.morphs.Plane())

    # Three rigid boxes stacked vertically
    box_size = (0.5, 0.5, 0.5)
    box_material = gs.materials.Rigid()

    # Bottom box
    box1 = scene.add_entity(
        morph=gs.morphs.Box(size=box_size, pos=(0.0, 0.0, 0.25)),
        material=box_material,
    )

    # Middle box
    box2 = scene.add_entity(
        morph=gs.morphs.Box(size=box_size, pos=(0.0, 0.0, 0.75)),
        material=box_material,
    )

    # Top box
    box3 = scene.add_entity(
        morph=gs.morphs.Box(size=box_size, pos=(0.0, 0.0, 1.25)),
        material=box_material,
    )

    scene.build()

    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()
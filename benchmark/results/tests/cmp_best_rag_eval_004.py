import numpy as np
import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, -3.0, 2.5),
            camera_lookat=(0.0, 0.0, 1.0),
            camera_fov=40,
        ),
        show_viewer=True,
    )

    scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 1.0),
            size=(0.3, 0.3, 0.3),
        ),
        material=gs.materials.Rigid(
            gravity_compensation=1.0,
        ),
    )

    scene.build()

    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
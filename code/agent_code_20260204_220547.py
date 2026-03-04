import genesis as gs
import numpy as np

def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(
            gravity=(0, 0, -9.8),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, 2.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=True,
    )

    ground = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.0),
            size=(10.0, 10.0, 0.1),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )

    ball = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 2.0),
            radius=0.2,
        ),
        material=gs.materials.Rigid(),
    )

    scene.build()

    for _ in range(2000):
        scene.step()

if __name__ == "__main__":
    main()
import torch

import genesis as gs


def main():
    ########################## init ##########################
    gs.init(precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(),
        viewer_options=gs.options.ViewerOptions(
            res=(1280, 720),
            camera_pos=(8.0, 5.0, 6.0),
            camera_lookat=(0.0, 0.0, 1.0),
            camera_fov=40,
        ),
        show_viewer=True,
    )

    ########################## entities ##########################
    # sphere (falling, pushed by wind)
    sphere = scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 5.0),
            radius=0.3,
        ),
        surface=gs.surfaces.Default(color=(0.2, 0.6, 1.0)),
    )

    # ground plane
    ground = scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.0),
            size=(10.0, 10.0, 0.1),
            fixed=True,
        ),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5)),
    )

    ########################## force fields ##########################
    wind = gs.force_fields.Wind(
        direction=(1.0, 0.0, 0.0),  # sideways push
        strength=5.0,               # constant acceleration magnitude
        radius=100.0,               # large enough to cover the falling path
        center=(0.0, 0.0, 0.0),
    )
    scene.add_force_field(wind)

    ########################## build and run ##########################
    scene.build()

    # simulate for a few seconds
    for _ in range(300):
        scene.step()

    # optional: keep viewer open after simulation ends
    if hasattr(scene.viewer, "run"):
        scene.viewer.run()


if __name__ == "__main__":
    main()
import torch

import genesis as gs


def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 3.0, 3.0),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
    )

    # Static floor
    scene.add_entity(gs.morphs.Plane())

    # Square fabric suspended in the air
    scene.add_entity(
        material=gs.materials.PBD.Cloth(),
        morph=gs.morphs.Mesh(
            file="meshes/cloth.obj",
            scale=1.0,
            pos=(0.0, 0.0, 1.5),
            euler=(0.0, 0.0, 0.0),
        ),
        surface=gs.surfaces.Default(
            color=(0.2, 0.4, 0.8, 1.0),
        ),
    )

    scene.build()

    # Run simulation
    for i in range(300):
        scene.step()


if __name__ == "__main__":
    main()
import torch

import genesis as gs


def main():
    ########################## init ##########################
    gs.init(precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        fem_options=gs.options.FEMOptions(),
        viewer_options=gs.options.ViewerOptions(
            res=(1280, 720),
            camera_pos=(5.0, 3.0, 3.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=True,
        show_FPS=True,
    )

    ########################## entities ##########################
    # Flat surface
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Plane(),
    )

    # Three squishy elastic spheres of different sizes in a row
    radii = [0.15, 0.1, 0.2]
    x_positions = [-0.5, 0.0, 0.5]
    drop_height = 1.5

    for radius, x_pos in zip(radii, x_positions):
        scene.add_entity(
            material=gs.materials.FEM.Elastic(
                E=50000.0,
                nu=0.3,
                rho=1000.0,
            ),
            morph=gs.morphs.Sphere(
                pos=(x_pos, 0.0, drop_height),
                radius=radius,
            ),
        )

    ########################## build ##########################
    scene.build()

    ########################## simulate ##########################
    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
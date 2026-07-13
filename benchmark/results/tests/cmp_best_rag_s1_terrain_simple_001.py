import genesis as gs
import numpy as np


def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 2.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
    )

    # Terrain parameters
    n_subterrains = (3, 3)
    subterrain_size = (1.0, 1.0)
    horizontal_scale = 0.1
    vertical_scale = 0.5

    terrain = scene.add_entity(
        gs.morphs.Terrain(
            n_subterrains=n_subterrains,
            subterrain_size=subterrain_size,
            horizontal_scale=horizontal_scale,
            vertical_scale=vertical_scale,
            subterrain_types="fractal_terrain",
        ),
    )

    sphere_radius = 0.1
    sphere_pos = np.array([0.0, 0.0, vertical_scale + sphere_radius + 0.01])
    sphere = scene.add_entity(
        gs.morphs.Sphere(
            radius=sphere_radius,
            pos=sphere_pos,
        ),
        material=gs.materials.Rigid(),
    )

    scene.build(n_envs=0)

    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
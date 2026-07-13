import numpy as np

import genesis as gs


def main():
    gs.init(backend=gs.gpu, precision="32")

    dt = 2e-2
    particle_size = 1e-2

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=dt,
            substeps=10,
        ),
        pbd_options=gs.options.PBDOptions(
            particle_size=particle_size,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, 3, 3),
            camera_lookat=(0, 0, 0.5),
        ),
    )

    # stationary table box
    table = scene.add_entity(
        material=gs.materials.Rigid(gravity_compensation=1.0),
        morph=gs.morphs.Box(
            pos=(0, 0, 0.025),
            size=(0.8, 0.8, 0.05),
        ),
    )

    # cloth tablecloth
    cloth = scene.add_entity(
        material=gs.materials.PBD.Cloth(),
        morph=gs.morphs.Mesh(
            file="meshes/cloth.obj",
            scale=2.0,
            pos=(0, 0, 0.55),
            euler=(0, 0, 0),
        ),
        surface=gs.surfaces.Default(
            color=(0.2, 0.4, 0.8, 1.0),
        ),
    )

    # several rigid cubes dropping from above
    num_cubes = 5
    for i in range(num_cubes):
        cube_size = 0.05
        x = np.random.uniform(-0.3, 0.3)
        y = np.random.uniform(-0.3, 0.3)
        z = 1.5 + i * 0.2  # staggered heights for varied impact
        scene.add_entity(
            material=gs.materials.Rigid(),
            morph=gs.morphs.Box(
                pos=(x, y, z),
                size=(cube_size, cube_size, cube_size),
            ),
        )

    scene.build()

    # run simulation
    horizon = 400
    for _ in range(horizon):
        scene.step()

    # optionally save video if viewer is running
    if scene.viewer.is_alive:
        scene.viewer.save_video("tablecloth.mp4")


if __name__ == "__main__":
    main()
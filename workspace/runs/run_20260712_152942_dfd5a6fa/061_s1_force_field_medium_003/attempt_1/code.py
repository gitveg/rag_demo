import argparse
import numpy as np
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2, -3, 1.5),
            camera_lookat=(0.0, 0.0, 0.3),
            camera_fov=40,
            max_FPS=60,
        ),
        sim_options=gs.options.SimOptions(
            dt=0.01,
        ),
        show_viewer=args.vis,
        show_FPS=False,
    )

    ########################## entities ##########################
    plane = scene.add_entity(
        gs.morphs.Plane(),
    )

    # Scattered light cubes
    num_cubes = 20
    cube_size = 0.04
    rng = np.random.default_rng(42)
    for i in range(num_cubes):
        x = rng.uniform(-1.0, 1.0)
        y = rng.uniform(-1.0, 1.0)
        z = cube_size / 2.0  # on the floor
        scene.add_entity(
            material=gs.materials.Rigid(rho=100),
            morph=gs.morphs.Box(
                pos=(x, y, z),
                size=(cube_size, cube_size, cube_size),
            ),
        )

    ########################## build ##########################
    scene.build()

    ########################## wind force field ##########################
    wind = gs.force_fields.Wind(
        direction=(1, 0, 0),   # horizontal push
        strength=5.0,
        radius=3.0,
        center=(0, 0, 0),
    )
    scene.add_force_field(wind)

    ########################## simulation ##########################
    for _ in range(300):
        scene.step()

    if args.vis:
        scene.viewer.stop()


if __name__ == "__main__":
    main()
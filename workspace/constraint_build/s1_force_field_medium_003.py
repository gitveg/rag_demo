import argparse
import numpy as np
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.0, -2.5, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # Floor
    scene.add_entity(gs.morphs.Plane())

    # Scatter small cubes on the floor
    np.random.seed(42)
    cube_size = 0.1
    for _ in range(20):
        x = np.random.uniform(-0.6, 0.6)
        z = np.random.uniform(-0.6, 0.6)
        pos = (x, cube_size / 2, z)  # y is upward
        cube = scene.add_entity(
            morph=gs.morphs.Box(size=(cube_size, cube_size, cube_size), pos=pos),
            material=gs.materials.Rigid(rho=100.0),
        )

    # Wind force field (horizontal, pushing +x direction)
    wind = gs.force_fields.Wind(
        direction=(1.0, 0.0, 0.0),
        strength=10.0,
        radius=2.0,
        center=(0.0, 0.0, 0.5),
    )
    scene.add_force_field(wind)
    wind.activate()

    scene.build()

    for i in range(500):
        scene.step()


if __name__ == "__main__":
    main()
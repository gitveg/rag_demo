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
            camera_pos=(0, -3.5, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
            max_FPS=60,
        ),
        sim_options=gs.options.SimOptions(
            dt=0.01,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    plane = scene.add_entity(gs.morphs.Plane())

    num_cubes = 20
    cube_size = 0.05
    np.random.seed(0)
    cubes = []
    for i in range(num_cubes):
        x = np.random.uniform(-1.5, 1.5)
        y = np.random.uniform(-1.5, 1.5)
        pos = (x, y, cube_size / 2)
        cube = scene.add_entity(
            gs.morphs.Box(pos=pos, size=(cube_size, cube_size, cube_size)),
            material=gs.materials.Rigid(rho=50.0),
        )
        cubes.append(cube)

    ########################## wind force field ##########################
    wind = gs.force_fields.Wind(
        direction=(1, 0, 0),
        strength=8.0,
        radius=10.0,
        center=(0, 0, 0),
    )
    scene.add_force_field(wind)

    ########################## build and simulate ##########################
    scene.build()

    for _ in range(1000):
        scene.step()

if __name__ == "__main__":
    main()
import argparse

import numpy as np

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(4.0, -3.0, 2.5),
        camera_lookat=(0.0, 0.0, 1.0),
        camera_fov=35,
        max_FPS=60,
    )

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.01,
        ),
        viewer_options=viewer_options,
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    terrain = scene.add_entity(
        gs.morphs.Terrain(
            type="fractal",
        ),
    )

    drone = scene.add_entity(
        morph=gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            model="CF2X",
            pos=(0.0, 0.0, 1.5),
        ),
    )

    ########################## force field ##########################
    turbulence = gs.force_fields.Turbulence(
        strength=2.0,
        frequency=5,
        flow=0.5,
        seed=42,
    )
    scene.add_force_field(turbulence)

    ########################## build ##########################
    scene.build()

    # Set propeller speeds to keep the drone hovering
    hover_rpm = 15000
    drone.set_propellels_rpm([hover_rpm] * 4)

    ########################## simulate ##########################
    for i in range(2000):
        scene.step()


if __name__ == "__main__":
    main()
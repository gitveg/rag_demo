import numpy as np

import genesis as gs


def main():
    ########################## init ##########################
    gs.init(backend=gs.cpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(5.0, -5.0, 2.5),
        camera_lookat=(0.0, 0.0, 1.0),
        camera_fov=40,
        max_FPS=60,
    )

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.01,
        ),
        viewer_options=viewer_options,
        show_viewer=True,
    )

    ########################## entities ##########################
    # Uneven terrain
    terrain = scene.add_entity(
        gs.morphs.Terrain(fractal_terrain=True),
    )

    # Crazyflie 2.X drone
    drone = scene.add_entity(
        morph=gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            model="CF2X",
            pos=(0.0, 0.0, 1.0),
        ),
    )

    ########################## build ##########################
    scene.build()

    ########################## add force field (turbulent wind) ##########################
    # Wind force field that will be modulated to simulate turbulence
    wind = gs.force_fields.Wind(
        direction=(1, 0, 0),
        strength=1.0,
        radius=10.0,
        center=(0, 0, 1.0),
    )
    scene.add_force_field(wind)

    ########################## run simulation ##########################
    for i in range(1000):
        # Simple turbulence: randomly change wind strength
        if i % 10 == 0:
            wind.strength = 0.5 + np.random.rand() * 1.5
        scene.step()


if __name__ == "__main__":
    main()
import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(2.5, 0.0, 1.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
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
    plane = scene.add_entity(
        gs.morphs.Plane(),
    )
    drone = scene.add_entity(
        morph=gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            model="CF2X",
            pos=(0.0, 0.0, 1.0),   # initial position with altitude 1 m
        ),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## flight control loop ##########################
    # Hover thrust estimation (mass * g for 30 g drone)
    hover_thrust = 0.3          # N
    pitch_cmd   = 0.1           # rad (≈5.7° forward tilt)
    yaw_rate    = 0.3           # rad/s, gives v = ω*R ≈ 0.6 m/s with R=2 m

    while True:
        scene.step()
        drone.set_attitude(
            thrust=hover_thrust,
            roll=0.0,
            pitch=pitch_cmd,
            yaw_rate=yaw_rate,
        )


if __name__ == "__main__":
    main()
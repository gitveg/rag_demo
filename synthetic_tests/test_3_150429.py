"""
User Query: Apply distinct static and dynamic friction coefficients to a rigid body, and set angular damping separately from linear damping to simulate a top spinning on a rough surface.
"""

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
            camera_lookat=(0.0, 0.0, 1.0),
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
    top = scene.add_entity(
        gs.morphs.Cylinder(
            pos=(0, 0, 1.0),
            radius=0.1,
            height=0.4,
        ),
        material=gs.materials.Rigid(
            linear_damping=0.1,
            angular_damping=0.3,
            static_friction=0.5,
            dynamic_friction=0.3,
        ),
    )

    ########################## build & run ##########################
    scene.build()

    if args.vis:
        while scene.viewer.running:
            scene.step()
            scene.viewer.render()
    else:
        for _ in range(1000):
            scene.step()


if __name__ == "__main__":
    main()
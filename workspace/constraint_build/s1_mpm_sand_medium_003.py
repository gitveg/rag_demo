import numpy as np

import genesis as gs


def main():
    gs.init(seed=0, precision="32", logging_level="info")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=3e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-2, -0.5, -2),
            upper_bound=(2, 3, 2),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5, -5, 5),
            camera_lookat=(0, 1, 0),
        ),
        show_viewer=True,
        show_FPS=False,
    )

    # Ground plane (large rigid box)
    ground = scene.add_entity(
        morph=gs.morphs.Box(pos=(0, -0.3, 0), size=(4, 0.6, 4)),
        material=gs.materials.Rigid(rho=1000.0, friction=0.5),
    )

    # Two sand blocks at different heights
    block1 = scene.add_entity(
        morph=gs.morphs.Box(pos=(-0.6, 2.0, 0), size=(0.6, 0.4, 0.6)),
        material=gs.materials.MPM.Sand(rho=2000.0, friction_angle=35),
    )

    block2 = scene.add_entity(
        morph=gs.morphs.Box(pos=(0.6, 3.5, 0), size=(0.6, 0.4, 0.6)),
        material=gs.materials.MPM.Sand(rho=2000.0, friction_angle=35),
    )

    scene.build()

    for i in range(1500):
        scene.step()


if __name__ == "__main__":
    main()
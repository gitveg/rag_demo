import argparse
import sys
import os
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    n_steps = 400 if "PYTEST_VERSION" not in os.environ else 2

    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="64")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=1 / 60),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, 1.5, 2.0),
            camera_lookat=(0.0, 0.2, 0.0),
        ),
        show_viewer=args.vis,
        show_FPS=True,
    )

    # Floor (static rigid box)
    floor = scene.add_entity(
        morph=gs.options.morphs.Box(
            size=(2.0, 0.1, 2.0),
            pos=(0.0, -0.05, 0.0),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )

    # Two soft cubes with different stiffness
    mat_stiff = gs.materials.FEM.Elastic(
        E=1e6,
        nu=0.2,
        rho=1000.0,
        model="linear",
    )
    mat_soft = gs.materials.FEM.Elastic(
        E=1e5,
        nu=0.2,
        rho=1000.0,
        model="linear",
    )

    cube_stiff = scene.add_entity(
        morph=gs.options.morphs.Box(
            size=(0.2, 0.2, 0.2),
            pos=(-0.3, 0.5, 0.0),
        ),
        material=mat_stiff,
    )

    cube_soft = scene.add_entity(
        morph=gs.options.morphs.Box(
            size=(0.2, 0.2, 0.2),
            pos=(0.3, 0.5, 0.0),
        ),
        material=mat_soft,
    )

    # Build the scene
    scene.build()

    # Simulation loop
    for i in range(n_steps):
        scene.step()

    # Keep viewer alive if visible
    if args.vis:
        scene.viewer.loop()


if __name__ == "__main__":
    main()
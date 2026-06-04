import argparse
import genesis as gs
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5.0, 3.0, 5.0),
            camera_lookat=(0.0, 0.0, 1.0),
        ),
        show_viewer=args.vis or True,
        rigid_options=gs.options.RigidOptions(),
        mpm_options=gs.options.MPMOptions(),
    )

    # Sloped terrain (rigid plane)
    terrain_material = gs.materials.Rigid()
    terrain = scene.add_entity(
        morph=gs.morphs.Plane(euler=(0.1745, 0.0, 0.0)),  # ~10° tilt about x-axis
        material=terrain_material,
    )

    # Sand material for the castle
    sand_material = gs.materials.MPM.Sand(E=1e6, rho=1500.0, friction_angle=35.0)
    castle = scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, 0.0, 0.3), size=(0.8, 0.8, 0.6)),
        material=sand_material,
    )

    # Heavy rigid block
    block_material = gs.materials.Rigid(rho=2000.0, friction=0.5)
    block = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 1.0, 0.3),
            size=(0.4, 0.4, 0.4),
            vel=(0.0, -3.0, 0.0),  # downhill velocity
        ),
        material=block_material,
    )

    scene.build()

    for i in range(500):
        scene.step()
        if i % 50 == 0:
            print(f"Step {i}")


if __name__ == "__main__":
    main()
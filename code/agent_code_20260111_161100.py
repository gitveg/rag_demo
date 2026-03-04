import argparse
import os

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()
    horizon = 50 if "PYTEST_VERSION" in os.environ else 1000

    gs.init(backend=gs.cpu, precision="32", performance_mode=True)

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.004,
        ),
        rigid_options=gs.options.RigidOptions(
            max_collision_pairs=200,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -3, 3),
            camera_lookat=(0.0, 0.0, 0.5),
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # Add rigid floor
    scene.add_entity(gs.morphs.Plane())

    # Add soft bunny (falling from above)
    bunny = gs.morphs.Mesh(
        asset_path="bunny.glb",
        position=(0.0, 0.0, 3.0),
        material=gs.materials.SoftMaterial(
            youngs_modulus=5e3,
            poissons_ratio=0.3,
            damping=0.1,
        ),
    )
    scene.add_entity(bunny)

    # Run simulation
    for _ in range(horizon):
        scene.step()


if __name__ == "__main__":
    main()
import argparse
import os

import genesis as gs
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -1, 1.5),
            camera_lookat=(0.0, 0.0, 0.0),
            camera_fov=30,
        ),
        show_viewer=args.vis,
        show_FPS=False,
    )

    ########################## create bumpy terrain ##########################
    # generate a random heightfield with some bumps
    np.random.seed(42)
    heightfield = np.random.uniform(-0.1, 0.1, (256, 256)).astype(np.float32)
    # smooth using simple averaging
    kernel = np.ones((3, 3)) / 9.0
    smooth = np.zeros_like(heightfield)
    for i in range(1, 255):
        for j in range(1, 255):
            smooth[i, j] = np.sum(heightfield[i-1:i+2, j-1:j+2] * kernel)
    heightfield = smooth * 0.3

    terrain_morph = gs.morphs.Terrain(
        heightfield=heightfield,
        pos=(0.0, 0.0, 0.0),
    )
    terrain = scene.add_entity(terrain_morph)

    ########################## create a soft deformable elastic sphere ##########################
    # Using sphere as a proxy for a cube (morphs.Box not in API)
    soft_morph = gs.morphs.Sphere(
        radius=0.07,
        pos=(0.5, 0.0, 0.2),
    )
    soft_material = gs.materials.FEM.Elastic(
        E=1e5,      # soft
        nu=0.4,
        rho=1000.0,
    )
    soft_body = scene.add_entity(soft_morph, material=soft_material)

    ########################## create robotic arm ##########################
    # Ensure the URDF file exists at the given path (example from Genesis repo)
    arm_path = os.path.join(
        os.path.dirname(gs.__file__), "..", "examples", "assets", "robots", "ur5", "ur5.urdf"
    )
    if not os.path.isfile(arm_path):
        # fallback to a generic name; user must adjust
        arm_path = "ur5.urdf"
    arm_morph = gs.morphs.URDF(
        file=arm_path,
        pos=(0.0, 0.0, 0.0),
        euler=(0.0, 0.0, 0.0),
        scale=1.0,
    )
    arm = scene.add_entity(arm_morph)

    ########################## build scene ##########################
    scene.build()

    ########################## simulation loop ##########################
    for i in range(1000):
        scene.step()

    if args.vis:
        scene.viewer.start()


if __name__ == "__main__":
    main()
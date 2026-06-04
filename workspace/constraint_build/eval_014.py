import argparse
import sys
import numpy as np
import genesis as gs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="64")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=1 / 60),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, -3.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=args.vis,
        show_FPS=args.vis,
    )

    # Large rigid box (static)
    rigid_morph = gs.morphs.Box(
        pos=(0.0, 0.0, 0.0),
        size=(2.0, 2.0, 2.0),
    )
    rigid_material = gs.materials.Rigid()
    rigid_entity = scene.add_entity(
        morph=rigid_morph,
        material=rigid_material,
    )

    # Soft elastic box (smaller, placed on top of rigid box)
    soft_morph = gs.morphs.Box(
        pos=(0.0, 0.0, 1.5),
        size=(1.0, 1.0, 1.0),
    )
    soft_material = gs.materials.FEM.Elastic(
        E=1e6,
        nu=0.2,
        rho=1000.0,
    )
    soft_entity = scene.add_entity(
        morph=soft_morph,
        material=soft_material,
    )

    scene.build()

    n_steps = 2000
    for i in range(n_steps):
        scene.step()
        if args.vis and i % 100 == 0:
            print(f"Step {i}")

if __name__ == "__main__":
    main()
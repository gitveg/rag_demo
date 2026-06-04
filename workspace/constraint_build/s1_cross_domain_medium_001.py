import argparse
import sys
import os
import genesis as gs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpu", action="store_true", default=(sys.platform == "darwin"))
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    n_steps = 500 if "PYTEST_VERSION" not in os.environ else 2

    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="64")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=1 / 60),
        vis_options=gs.options.VisOptions(show_world_frame=True),
        viewer_options=gs.options.ViewerOptions(camera_pos=(0.5, 0.5, 1.5)),
    )

    # Soft elastic sheet (horizontal)
    sheet_morph = gs.morphs.Box(pos=(0.0, 0.0, 0.0), size=(2.0, 0.02, 2.0))
    sheet_material = gs.materials.FEM.Cloth(
        E=1e5,
        nu=0.45,
        rho=100.0,
        thickness=0.01,
    )
    sheet = scene.add_entity(
        morph=sheet_morph,
        material=sheet_material,
    )

    # Rigid sphere
    sphere_morph = gs.morphs.Sphere(pos=(0.0, 0.5, 0.0), radius=0.1)
    sphere_material = gs.materials.Rigid(rho=1000.0)
    sphere = scene.add_entity(
        morph=sphere_morph,
        material=sphere_material,
    )

    scene.build()

    for i in range(n_steps):
        scene.step(update_visualizer=args.vis, refresh_visualizer=args.vis)

if __name__ == "__main__":
    main()
import argparse
import os

import genesis as gs
import numpy as np
from genesis.utils.terrain import mesh_to_heightfield


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
            camera_pos=(0, -50, 0),
            camera_lookat=(0, 0, 0),
        ),
        show_viewer=args.vis,
    )

    # ---- sandy desert terrain (heightfield from included mesh) ----
    horizontal_scale = 2.0
    gs_root = os.path.dirname(os.path.abspath(gs.__file__))
    path_terrain = os.path.join(gs_root, "assets", "meshes", "terrain_45.obj")
    hf_terrain, xs, ys = mesh_to_heightfield(path_terrain, spacing=horizontal_scale, oversample=1)

    scene.add_entity(
        morph=gs.morphs.Terrain(height_field=hf_terrain),
        material=gs.materials.Rigid(),
    )

    # ---- drone ----
    drone = scene.add_entity(
        morph=gs.morphs.Drone(
            file="urdf/drones/cf2x.urdf",
            pos=(0.0, 0, 2.0),  # start above the terrain
        ),
    )

    # ---- wind force field (strong gust occasionally) ----
    wind = gs.force_fields.Wind(
        direction=(1, 0, 0),   # push right
        strength=5.0,
        radius=200.0,          # cover large area so drone stays inside
        center=(0, 0, 2.0),
    )
    scene.add_force_field(wind)

    ########################## build ##########################
    scene.build()

    ########################## simulation loop ##########################
    for i in range(1000):
        # toggle strong wind every 200 steps to simulate occasional gust
        if (i // 200) % 2 == 0:
            wind.strength = 5.0
        else:
            wind.strength = 0.0

        scene.step()


if __name__ == "__main__":
    main()
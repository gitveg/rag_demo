"""
User Query: Create a composite rigid body from multiple convex hulls with non-uniform density distribution and apply a local center of mass offset.
"""

import argparse
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.0, -2, 1.5),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=args.vis,
    )

    plane = gs.morphs.MeshSet(
        path="plane.obj",
        convexify=False,
        decimate=False,
    )
    scene.add_entity(
        morph=plane,
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(),
        pose=gs.Pose(position=(0.0, 0.0, 0.0)),
    )

    composite_mesh = gs.morphs.MeshSet(
        path="composite.obj",
        convexify=True,
        decompose_nonconvex=True,
    )
    scene.add_entity(
        morph=composite_mesh,
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(),
        pose=gs.Pose(position=(0.0, 0.0, 0.5)),
    )

    scene.build(n_envs=0)
    for _ in range(100):
        scene.step()


if __name__ == "__main__":
    main()
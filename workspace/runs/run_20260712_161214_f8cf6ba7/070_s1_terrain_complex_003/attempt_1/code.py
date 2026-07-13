import genesis as gs
import os


def main():
    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -50, 0),
            camera_lookat=(0, 0, 0),
        ),
        show_viewer=True,
    )

    gs_root = os.path.dirname(os.path.abspath(gs.__file__))
    path_terrain = os.path.join(gs_root, "assets", "meshes", "terrain_45.obj")

    scene.add_entity(
        morph=gs.morphs.Mesh(
            file=path_terrain,
            fixed=True,
        ),
    )

    scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.0, 10.0, 0.0),
            radius=0.5,
        ),
        material=gs.materials.Rigid(),
    )

    scene.build()

    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
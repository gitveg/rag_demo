"""
User Query: Adjust the camera's field of view and clipping planes in the viewer to extreme values for a macro simulation view, and lock the camera to track a specific body's centroid.
"""

import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--fix", action="store_true", default=False)
    args = parser.parse_args()

    gs.init()

    scene = gs.Scene(
        vis_options=gs.options.VisOptions(
            rendered_envs_idx=(0,),
        ),
        profiling_options=gs.options.ProfilingOptions(
            show_FPS=False,
        ),
        show_viewer=True,
    )
    scene.add_entity(morph=gs.morphs.Plane())
    box = scene.add_entity(
        gs.morphs.Box(
            size=(0.1, 0.1, 0.1),
            pos=(0.0, -0.9, 1.0),
            euler=(15.0, 30.0, 60.0),
        )
    )

    cam = scene.add_camera(
        res=(640, 480),
        pos=(2.0, 0.0, 1.5),
        lookat=(0, 0, 0.7),
        fov=10,
        near=0.001,
        far=1000.0,
        GUI=True,
    )
    cam.follow_entity(box, fix_orientation=args.fix)

    scene.build()

    box.set_dofs_velocity([0.0, 5.0, 0.0, 0.0, 0.0, 1.0])
    for _ in range(100):
        scene.step()


if __name__ == "__main__":
    main()
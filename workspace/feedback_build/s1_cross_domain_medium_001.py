import argparse

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu, logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            substeps=10,
            gravity=(0, 0, -9.8),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2, 2, 1.5),
            camera_lookat=(0, 0, 0.2),
            camera_up=(0, 0, 1),
        ),
        show_viewer=args.vis,
    )

    ########################## materials ##########################
    mat_rigid = gs.materials.Rigid()
    mat_soft = gs.materials.PBD.Elastic(
        rho=500.0,
        stretch_compliance=0.01,
        volume_compliance=0.01,
    )

    ########################## entities ##########################
    # rigid floor to support the soft sheet
    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=mat_rigid,
    )

    # thin soft sheet resting on the floor
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.01),
            size=(0.5, 0.5, 0.02),
        ),
        material=mat_soft,
    )

    # rigid falling sphere
    scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 0.3),
            radius=0.05,
        ),
        material=mat_rigid,
        surface=gs.surfaces.Default(color=(1.0, 0.5, 0.5)),
    )

    ########################## build & simulate ##########################
    scene.build()

    if args.vis:
        scene.start_recording()

    for _ in range(300):
        scene.step()

    if args.vis:
        scene.viewer.save_video("sphere_on_sheet.mp4")


if __name__ == "__main__":
    main()
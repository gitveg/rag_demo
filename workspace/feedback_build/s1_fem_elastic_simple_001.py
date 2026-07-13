import argparse
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5.0, -5.0, 4.0),
            camera_lookat=(0.0, 0.0, 1.0),
        ),
        show_viewer=args.vis,
    )

    # ground plane with no friction
    frictionless_rigid = gs.materials.Rigid(friction=0.0)
    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=frictionless_rigid,
    )

    # soft elastic ball
    scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 3.0),
            radius=0.5,
        ),
        material=gs.materials.FEM.Elastic(),
    )

    scene.build(n_envs=0)

    if args.vis:
        scene.start_recording()

    for i in range(300):
        scene.step()
        if i % 30 == 0:
            print(f"Step {i}")

    if args.vis:
        scene.viewer.save_video("soft_ball_bounce.mp4")
        scene.viewer.close()


if __name__ == "__main__":
    main()
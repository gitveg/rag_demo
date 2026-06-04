import argparse
import genesis as gs

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
            camera_pos=(5.0, 0.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=True,
    )

    ########################## add entities ##########################
    # ground (tank)
    scene.add_entity(
        morph=gs.options.morphs.Mesh(
            file="meshes/tank.obj",
            scale=1.0,
        ),
    )
    # ball
    scene.add_entity(
        morph=gs.options.morphs.Sphere(
            radius=0.15,
            pos=(0.0, 0.0, 0.8),
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build ##########################
    scene.build()

    ########################## record video ##########################
    scene.start_recording()
    for _ in range(300):
        scene.step()
    scene.viewer.save_video(filename="output.mp4")

if __name__ == "__main__":
    main()
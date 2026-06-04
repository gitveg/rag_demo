import genesis as gs

def main():
    # init genesis
    gs.init(backend=gs.gpu)

    # create scene with viewer options for 45-degree angle
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 3.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
    )

    # add a static ground plane (box morph)
    ground = scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(0.0, 0.0, -0.25),
            size=(4.0, 4.0, 0.5),
        ),
        material=gs.materials.Rigid(),
    )

    # add a red sphere (color not directly set via API, default is grey)
    sphere = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(0.0, 0.0, 2.0),
            radius=0.3,
        ),
        material=gs.materials.Rigid(),
    )

    # build the scene
    scene.build()

    # start recording video
    scene.start_recording()

    # run simulation for 200 steps
    for _ in range(200):
        scene.step()

    # save video
    scene.viewer.save_video(filename='sphere_fall.mp4')

    # stop recording
    scene.stop_recording()

if __name__ == '__main__':
    main()
import genesis as gs

def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(
            gravity=(0.0, 0.0, -9.81),
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.5, -0.5, 0.0),
            upper_bound=(0.5, 0.5, 1.0),
        ),
        viewer_options=gs.options.ViewerOptions(
            res=(1280, 720),
            camera_pos=(2.0, 2.0, 1.5),
            camera_lookat=(0.0, 0.0, 0.4),
            camera_fov=50,
        ),
        show_viewer=True,
    )

    # tank of water
    scene.add_entity(
        material=gs.materials.MPM.Liquid(sampler="regular"),
        morph=gs.morphs.Box(
            lower=(-0.5, -0.5, 0.0),
            upper=(0.5, 0.5, 0.6),
        ),
        surface=gs.surfaces.Default(
            color=(0.3, 0.6, 1.0, 0.8),
        ),
    )

    # heavy rigid metallic sphere
    scene.add_entity(
        material=gs.materials.Rigid(rho=8000),
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 1.0),
            radius=0.1,
        ),
        surface=gs.surfaces.Default(
            color=(0.8, 0.8, 0.8, 1.0),
        ),
    )

    scene.build(n_envs=0)

    scene.start_recording()
    for _ in range(500):
        scene.step()
    scene.viewer.save_video(filename='splash_and_sink.mp4')

if __name__ == "__main__":
    main()
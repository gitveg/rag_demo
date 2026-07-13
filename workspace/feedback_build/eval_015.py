import genesis as gs

def main():
    ########################## init ##########################
    gs.init(precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=20,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.5, -0.5, -0.1),
            upper_bound=(0.5, 0.5, 1.0),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 1.0, 0.8),
            camera_lookat=(0.0, 0.0, 0.2),
            camera_fov=30,
            max_FPS=120,
        ),
        show_viewer=True,
    )

    ########################## add entities ##########################
    # static flat ground
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Plane(fixed=True),
        surface=gs.surfaces.Default(color=(0.7, 0.7, 0.7, 1.0)),
    )

    # block of liquid water
    scene.add_entity(
        material=gs.materials.MPM.Liquid(),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.5),
            size=(0.2, 0.2, 0.2),
        ),
        surface=gs.surfaces.Default(color=(0.3, 0.5, 1.0, 1.0)),
    )

    ########################## build and simulate ##########################
    scene.build()

    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()
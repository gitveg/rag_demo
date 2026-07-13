import genesis as gs

def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=3e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.5, 0.0, -0.5),
            upper_bound=(0.5, 2.0, 0.5),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, 1.5, 1.5),
            camera_lookat=(0.0, 0.5, 0.0),
        ),
        vis_options=gs.options.VisOptions(
            visualize_mpm_boundary=True,
        ),
        show_viewer=True,
    )

    scene.add_entity(
        material=gs.materials.MPM.Sand(),
        morph=gs.morphs.Box(
            pos=(0.0, 0.3, 0.0),
            size=(0.15, 0.15, 0.15),
        ),
        surface=gs.surfaces.Rough(
            color=(0.8, 0.7, 0.5, 1.0),
            vis_mode="particle",
        ),
    )

    scene.add_entity(
        material=gs.materials.MPM.Sand(),
        morph=gs.morphs.Box(
            pos=(0.0, 1.0, 0.0),
            size=(0.15, 0.15, 0.15),
        ),
        surface=gs.surfaces.Rough(
            color=(0.8, 0.7, 0.5, 1.0),
            vis_mode="particle",
        ),
    )

    scene.build()

    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()
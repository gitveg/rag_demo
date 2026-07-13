import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=3e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.5, -0.5, -0.1),
            upper_bound=(0.5, 0.5, 1.0),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, 0.5, 1.5),
            camera_lookat=(0.0, 0.0, 0.2),
            camera_fov=40,
            max_FPS=60,
        ),
        vis_options=gs.options.VisOptions(
            visualize_mpm_boundary=True,
        ),
    )

    # Ground plane
    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(),
    )

    # Initial pile of dry sand released above the ground
    sand = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.5),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.MPM.Sand(),
        surface=gs.surfaces.Rough(
            color=(0.9, 0.8, 0.5, 1.0),
        ),
    )

    scene.build()

    # Run simulation to let sand fall and form a cone
    for _ in range(2000):
        scene.step()

if __name__ == "__main__":
    main()
import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-1.0, -1.0, 0.0),
            upper_bound=(1.0, 1.0, 1.5),
        ),
        vis_options=gs.options.VisOptions(
            visualize_mpm_boundary=True,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, 1.5, 1.2),
            camera_lookat=(0.0, 0.0, 0.2),
            camera_fov=30,
            res=(960, 640),
        ),
        show_viewer=True,
    )

    # Shallow basin floor
    scene.add_entity(
        morph=gs.options.morphs.Box(pos=(0, 0, 0.05), size=(1.5, 1.5, 0.1)),
        material=gs.materials.Rigid(needs_coup=True),
    )

    # Basin walls
    wall_height = 0.2
    wall_thickness = 0.05
    half_size = 0.75

    walls = [
        (0, half_size, 1.5, wall_thickness),       # front
        (0, -half_size, 1.5, wall_thickness),      # back
        (-half_size, 0, wall_thickness, 1.5),      # left
        (half_size, 0, wall_thickness, 1.5),       # right
    ]
    for dx, dy, sx, sy in walls:
        scene.add_entity(
            morph=gs.options.morphs.Box(
                pos=(dx, dy, wall_height / 2 + 0.1),
                size=(sx, sy, wall_height),
            ),
            material=gs.materials.Rigid(needs_coup=True),
        )

    # Water blob
    scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(0, 0, 0.8),
            size=(0.3, 0.3, 0.3),
        ),
        material=gs.materials.MPM.Liquid(),
    )

    scene.build()

    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
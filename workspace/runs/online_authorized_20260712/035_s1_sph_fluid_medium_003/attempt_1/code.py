import argparse
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(seed=0, precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=20,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.35, -0.35, -0.02),
            upper_bound=(0.35, 0.35, 0.6),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, 0.8, 1.0),
            camera_lookat=(0.0, 0.0, 0.25),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    ########################## add tank (transparent cubical) ##########################
    wall_thickness = 0.01
    tank_size = 0.5
    half_size = tank_size / 2

    # bottom
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, wall_thickness / 2),
            size=(tank_size, tank_size, wall_thickness),
        ),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5, 0.3)),
    )
    # left wall
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            pos=(-half_size, 0.0, half_size),
            size=(wall_thickness, tank_size, tank_size),
        ),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5, 0.3)),
    )
    # right wall
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            pos=(half_size, 0.0, half_size),
            size=(wall_thickness, tank_size, tank_size),
        ),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5, 0.3)),
    )
    # front wall
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            pos=(0.0, -half_size, half_size),
            size=(tank_size, wall_thickness, tank_size),
        ),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5, 0.3)),
    )
    # back wall
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            pos=(0.0, half_size, half_size),
            size=(tank_size, wall_thickness, tank_size),
        ),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5, 0.3)),
    )

    ########################## add liquid (half filled) ##########################
    liquid_level = tank_size / 2  # fill halfway, i.e., 0.25 m
    liquid_margin = 0.01  # slight gap to avoid initial wall overlap
    liquid_size = tank_size - 2 * liquid_margin

    scene.add_entity(
        material=gs.materials.MPM.Liquid(),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, liquid_level / 2),
            size=(liquid_size, liquid_size, liquid_level),
        ),
        surface=gs.surfaces.Default(
            color=(0.3, 0.3, 1.0),
            vis_mode="particle",
        ),
    )

    ########################## build and simulate ##########################
    scene.build()

    if args.vis:
        # run until viewer is closed
        while scene.viewer.is_alive():
            scene.step()
    else:
        # headless simulation for a few seconds
        for _ in range(500):
            scene.step()


if __name__ == "__main__":
    main()
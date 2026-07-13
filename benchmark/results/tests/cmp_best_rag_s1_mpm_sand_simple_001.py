import genesis as gs


def main():
    ########################## init ##########################
    gs.init(precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-1.0, -1.0, 0.0),
            upper_bound=(1.0, 1.0, 2.0),
        ),
        vis_options=gs.options.VisOptions(
            visualize_mpm_boundary=True,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_fov=40,
            res=(800, 600),
        ),
        show_viewer=True,
    )

    ########################## add ground ##########################
    plane = scene.add_entity(
        morph=gs.options.morphs.Plane(),
        material=gs.materials.Rigid(rho=200.0, friction=0.8),
    )

    ########################## add sand pile ##########################
    sand = scene.add_entity(
        morph=gs.options.morphs.Cylinder(
            pos=(0.0, 0.0, 1.0),
            radius=0.3,
            height=0.2,
        ),
        material=gs.materials.MPM.ElastoPlastic(
            rho=1500.0,  # dry sand density
        ),
        surface=gs.options.surfaces.Default(),
    )

    ########################## build and simulate ##########################
    scene.build()

    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
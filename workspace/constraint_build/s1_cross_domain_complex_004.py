import argparse
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1e-2,
            substeps=10,
        ),
        sph_options=gs.options.SPHOptions(
            lower_bound=(0.0, -0.5, 0.0),
            upper_bound=(0.8, 0.5, 0.8),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, 1.5, 1.5),
            camera_lookat=(0.4, 0.0, 0.4),
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # tank bottom plane
    bottom = scene.add_entity(
        morph=gs.options.morphs.Plane(
            pos=(0.4, -0.5, 0.4),
            euler=(0.0, 0.0, 0.0),
        ),
        material=gs.materials.Rigid(rho=1000.0),
        visualize_contact=False,
    )

    # heavy metallic sphere (approximated as a small cube)
    sphere = scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(0.4, 0.3, 0.4),
            size=(0.06, 0.06, 0.06),
        ),
        material=gs.materials.Rigid(
            rho=7800.0,
            friction=0.5,
        ),
    )

    # water fluid emitter
    emitter = scene.add_emitter(
        material=gs.materials.SPH.Liquid(
            rho=1000.0,
            stiffness=50000.0,
            exponent=7.0,
            mu=0.005,
            gamma=0.01,
        ),
        max_particles=60000,
    )

    ########################## build ##########################
    scene.build()

    ########################## simulate ##########################
    for i in range(1500):
        scene.step()


if __name__ == "__main__":
    main()
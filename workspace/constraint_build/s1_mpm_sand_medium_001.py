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
            camera_pos=(3.5, -2.0, 3.0),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # ground plane
    ground = scene.add_entity(
        morph=gs.options.morphs.Terrain(),
        material=gs.materials.Rigid(),
    )

    # container (tank) – tilted so it will "tip over"
    container = scene.add_entity(
        morph=gs.options.morphs.Mesh(
            file="tank",
            scale=1.0,
            pos=(0.0, 0.0, 0.3),
            euler=(0.0, 0.3, 0.0),  # rotate around y-axis
        ),
        material=gs.materials.Rigid(),
    )

    # sand particles inside the container
    sand = scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(0.0, 0.0, 0.6),
            radius=0.2,
        ),
        material=gs.materials.MPM.Sand(
            E=1e6,
            nu=0.2,
            rho=2000.0,
            friction_angle=35,
        ),
    )

    ########################## build ##########################
    scene.build()

    ########################## run simulation ##########################
    for i in range(500):
        scene.step()


if __name__ == "__main__":
    main()
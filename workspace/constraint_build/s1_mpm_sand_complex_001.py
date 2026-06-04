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
            camera_pos=(2.0, 1.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
        show_FPS=True,
    )

    ########################## hourglass container ##########################
    # Load hourglass mesh and set glass surface
    hourglass = scene.add_entity(
        morph=gs.options.morphs.Mesh(
            file="hourglass.obj",
            scale=0.5,
        ),
        material=gs.materials.Rigid(),
        surface=gs.options.surfaces.Glass(),
    )

    ########################## sand in upper half ##########################
    # Initial sand block in the top half of the hourglass
    sand_material = gs.materials.MPM.Sand(rho=2000.0, friction_angle=35)
    sand = scene.add_entity(
        morph=gs.options.morphs.Box(
            size=(0.4, 0.4, 0.3),
            pos=(0.0, 0.3, 0.0),
        ),
        material=sand_material,
    )

    ########################## build scene ##########################
    scene.build()

    ########################## run simulation ##########################
    for i in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
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
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=args.vis,
    )

    ########################## add a sphere ##########################
    scene.add_entity(
        morph=gs.options.morphs.Sphere(
            radius=0.5,
            pos=(0.0, 0.5, 0.0),
        ),
        material=gs.materials.Rigid(),
    )

    ########################## build the scene ##########################
    scene.build()

    ########################## add constant upward force field to counteract gravity ##########################
    # default gravity is -9.81 m/s^2 in y direction
    force_field = gs.force_fields.Constant(direction=(0, 1, 0), strength=9.81)
    scene.add_force_field(force_field)

    ########################## simulation loop ##########################
    for i in range(1000):
        scene.step(update_visualizer=args.vis)

if __name__ == "__main__":
    main()
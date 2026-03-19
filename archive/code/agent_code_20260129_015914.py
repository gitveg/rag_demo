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
            camera_pos=(5.0, 5.0, 5.0),
            camera_lookat=(0.0, 0.0, 2.0),
            camera_fov=45,
        ),
        show_viewer=args.vis,
        rigid_options=gs.options.RigidOptions(
            # 使用了不存在的 gs.constraint_solver.SAP，直接采用默认值即可
            constraint_solver=gs.constraint_solver.SAP,
        ),
    )

    ########################## entities ##########################
    # Ground plane
    ground = scene.add_entity(
        gs.morphs.Box(
            size=(20.0, 20.0, 0.2),
            fixed=True,
            pos=(0.0, 0.0, 0.0),
        ),
    )

    # Falling sphere
    sphere = scene.add_entity(
        gs.morphs.Sphere(
            radius=0.5,
            fixed=False,
            pos=(0.0, 0.0, 5.0),
            material=gs.materials.Rigid(density=500.0),
        ),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## simulation loop ##########################
    for _ in range(500):
        scene.step()

    print("Simulation complete.")


if __name__ == "__main__":
    main()
import genesis as gs


def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
            constraint_solver=gs.constraint_solver.CG,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(10, -10, 10),
            camera_lookat=(0, 0, 0),
        ),
    )

    # Large terrain with procedurally generated rolling hills and valleys
    terrain = scene.add_entity(
        gs.morphs.Terrain(
            visualization=True,
            n_subterrains=(1, 1),
            subterrain_size=(20.0, 20.0),
        ),
    )

    # Rigid box placed above a sloped region of the terrain
    box = scene.add_entity(
        gs.morphs.Box(
            pos=(2.0, 2.0, 2.0),  # (x, y) on the slope, z just above
            size=(0.5, 0.5, 0.5),
            fixed=False,
        ),
    )

    scene.build()

    # Run simulation: the box will fall, land on the sloped terrain, and slide down
    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
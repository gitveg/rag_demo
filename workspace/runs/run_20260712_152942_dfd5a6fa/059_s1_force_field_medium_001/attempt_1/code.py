import genesis as gs

def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(
            gravity=(0.0, 0.0, -9.81),  # standard gravity downward
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5.0, 5.0, 5.0),
            camera_lookat=(0.0, 0.0, 1.0),
        ),
        show_viewer=True,
    )

    # ground plane
    plane = scene.add_entity(
        morph=gs.morphs.Plane(
            pos=(0.0, 0.0, 0.0),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )

    # three spheres at different heights
    x_positions = [-1.0, 0.0, 1.0]
    heights = [3.0, 2.5, 2.0]  # z coordinate

    spheres = []
    for i, (x, z) in enumerate(zip(x_positions, heights)):
        # middle sphere gets gravity compensation to float
        if i == 1:
            mat = gs.materials.Rigid(gravity_compensation=1.0)  # exactly cancels gravity
        else:
            mat = gs.materials.Rigid()  # default, falls normally

        s = scene.add_entity(
            morph=gs.morphs.Sphere(
                pos=(x, 0.0, z),
                radius=0.2,
            ),
            material=mat,
        )
        spheres.append(s)

    scene.build(n_envs=0)

    # simulation loop
    try:
        for _ in range(500):
            scene.step()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
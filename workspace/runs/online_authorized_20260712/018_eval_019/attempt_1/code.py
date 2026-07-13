import genesis as gs

def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(gravity=(0, 0, -9.81)),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, -2.0, 2.0),
            camera_lookat=(1.0, 0.0, 0.5),
            camera_fov=60,
        ),
    )

    # Ground plane
    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8)),
    )

    # Tilted ramp (static box)
    ramp_size = (2.0, 0.5, 0.05)
    ramp_pos = (0.0, 0.0, 0.3)
    ramp_euler = (0.0, -30.0, 0.0)
    scene.add_entity(
        morph=gs.morphs.Box(
            size=ramp_size,
            pos=ramp_pos,
            euler=ramp_euler,
            fixed=True,
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.4, 0.4, 0.4)),
    )

    # Rolling sphere
    sphere_radius = 0.15
    sphere_pos = (0.7, 0.0, 0.6)  # start high on the ramp
    scene.add_entity(
        morph=gs.morphs.Sphere(
            radius=sphere_radius,
            pos=sphere_pos,
        ),
        material=gs.materials.Rigid(rho=500),
        surface=gs.surfaces.Default(color=(1.0, 0.0, 0.0)),
    )

    # Stack of three boxes
    box_size = (0.2, 0.2, 0.2)
    stack_z_base = 0.1  # bottom box center z
    stack_increment = 0.2  # height of each box
    stack_x = 1.2  # x coordinate beyond ramp
    for i in range(3):
        z = stack_z_base + i * stack_increment
        scene.add_entity(
            morph=gs.morphs.Box(
                size=box_size,
                pos=(stack_x, 0.0, z),
            ),
            material=gs.materials.Rigid(),
            surface=gs.surfaces.Default(color=(0.0, 0.8, 0.0)),
        )

    scene.build()

    # Run simulation
    while scene.viewer.is_alive():  # run until viewer window closed
        scene.step()

if __name__ == "__main__":
    main()
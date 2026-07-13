import genesis as gs

def main():
    gs.init(precision="32", logging_level="info")

    # Create scene with gravity and PBD solver enabled
    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(gravity=(0, 0, -9.81)),
        pbd_options=gs.options.PBDOptions(),
        viewer_options=gs.options.ViewerOptions(
            res=(1280, 720),
            camera_pos=(5.0, 5.0, 4.0),
            camera_lookat=(0.0, 0.0, 1.0),
            camera_fov=40,
        ),
        show_viewer=True,
    )

    # Flat surface (plane) as the ground
    scene.add_entity(gs.morphs.Plane())

    # Three squishy elastic spheres of different sizes in a row
    sphere_radii = [0.5, 0.7, 0.3]
    x_positions = [-2.0, 0.0, 2.0]
    drop_height = 2.0

    for x, radius in zip(x_positions, sphere_radii):
        material = gs.materials.PBD.Elastic(
            rho=1000.0,
            stretch_compliance=1e-4,
            bending_compliance=1e-4,
            volume_compliance=1e-5,
        )
        morph = gs.morphs.Sphere(
            pos=(x, 0.0, drop_height),
            radius=radius,
        )
        scene.add_entity(material=material, morph=morph)

    scene.build()

    # Run simulation
    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()
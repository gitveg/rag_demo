import genesis as gs

def main():
    gs.init(backend=gs.cpu)

    scene = gs.Scene(
        show_viewer=True,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 2.0, 2.0),
            camera_lookat=(0.0, 0.0, 1.0),
        ),
    )

    # Ground plane for reference
    scene.add_entity(
        morph=gs.morphs.Plane(),
    )

    # Lightweight sphere suspended in the air
    scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 1.0),
            radius=0.1,
        ),
        material=gs.materials.Rigid(
            rho=10.0,                  # low density = lightweight
            gravity_compensation=1.0,  # cancel gravity -> suspended
        ),
        surface=gs.surfaces.Default(color=(1.0, 0.5, 0.5, 1.0)),
    )

    # Sideways wind force field (constant acceleration along +x)
    wind = gs.force_fields.Wind(
        direction=(1.0, 0.0, 0.0),
        strength=2.0,
        center=(0.0, 0.0, 1.0),  # aligned with the sphere
        radius=2.0,               # covers the sphere
    )
    scene.add_force_field(wind)

    scene.build()

    # Run the simulation
    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()
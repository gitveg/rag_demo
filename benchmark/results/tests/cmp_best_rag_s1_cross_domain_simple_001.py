import genesis as gs

def main():
    gs.init(backend=gs.gpu, precision="32", logging_level="info")

    # Create scene with SPH solver for water
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1e-2,
            substeps=10,
        ),
        sph_options=gs.options.SPHOptions(
            lower_bound=(-0.5, -0.5, 0.0),
            upper_bound=(0.5, 0.5, 0.5),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_fov=45,
            res=(1280, 720),
        ),
        show_viewer=True,
    )

    # Ground plane (container bottom)
    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(),
        surface=gs.options.surfaces.Default(color=(0.5, 0.5, 0.5, 1.0))
    )

    # Water volume (initial block of particles)
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, 0.0, 0.1), size=(1.0, 1.0, 0.2)),
        material=gs.materials.SPH.Liquid(),
        surface=gs.options.surfaces.Default(color=(0.2, 0.4, 0.8, 0.7))
    )

    # Dropped rigid sphere
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(radius=0.1, pos=(0.0, 0.0, 0.4)),
        material=gs.materials.Rigid(),
        surface=gs.options.surfaces.Default(color=(1.0, 0.0, 0.0, 1.0))
    )

    scene.build()

    # Run simulation for a number of steps to observe splash
    for _ in range(2000):
        scene.step()

if __name__ == "__main__":
    main()
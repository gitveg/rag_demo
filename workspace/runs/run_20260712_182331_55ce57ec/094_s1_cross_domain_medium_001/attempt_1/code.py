import genesis as gs


def main():
    gs.init(backend=gs.gpu, precision="64")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1 / 60,
            substeps=2,
        ),
        fem_options=gs.options.FEMOptions(
            use_implicit_solver=True,
        ),
        coupler_options=gs.options.SAPCouplerOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2, -2, 1.5),
            camera_lookat=(0, 0, 0.3),
            max_FPS=60,
        ),
        show_viewer=True,
    )

    # Rigid ground plane
    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(),
    )

    # Soft elastic sheet (thin box resting on the plane)
    scene.add_entity(
        material=gs.materials.FEM.Elastic(
            E=100000,
            nu=0.3,
            rho=500,
        ),
        morph=gs.morphs.Box(
            pos=(0, 0, 0.015),
            size=(0.8, 0.8, 0.02),
        ),
        surface=gs.surfaces.Default(color=(0.8, 0.3, 0.3)),
    )

    # Rigid sphere falling onto the sheet
    scene.add_entity(
        material=gs.materials.Rigid(rho=5000),
        morph=gs.morphs.Sphere(
            pos=(0, 0, 0.8),
            radius=0.12,
        ),
        surface=gs.surfaces.Default(color=(0.3, 0.5, 1.0)),
    )

    scene.build()

    for _ in range(300):
        scene.step()


if __name__ == "__main__":
    main()
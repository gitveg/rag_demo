import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=1 / 60,
            substeps=10,
        ),
        fem_options=gs.options.FEMOptions(),
        coupler_options=gs.options.SAPCouplerOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.8),
        ),
        show_viewer=True,
    )

    # Platform
    scene.add_entity(
        gs.options.morphs.Plane(),
        material=gs.materials.Rigid(),
    )

    # Soft elastic bunny
    scene.add_entity(
        gs.options.morphs.Mesh(
            file="meshes/bunny.obj",
            pos=(0, 0, 0.5),
            scale=3.0,
        ),
        material=gs.materials.FEM.Elastic(
            E=50000.0,
            nu=0.3,
            rho=500.0,
        ),
    )

    # Rigid metal spheres dropped from different heights
    sphere_configs = [
        dict(pos=(0.3, 0.3, 1.5), radius=0.08),
        dict(pos=(-0.3, -0.2, 2.0), radius=0.08),
        dict(pos=(0.1, -0.35, 2.5), radius=0.08),
        dict(pos=(-0.2, 0.25, 1.8), radius=0.08),
    ]
    for cfg in sphere_configs:
        scene.add_entity(
            gs.options.morphs.Sphere(
                pos=cfg["pos"],
                radius=cfg["radius"],
            ),
            material=gs.materials.Rigid(rho=5000.0),
        )

    scene.build()

    for _ in range(600):
        scene.step()


if __name__ == "__main__":
    main()
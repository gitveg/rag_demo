import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=3e-3,
            substeps=10,
        ),
        rigid_options=gs.options.RigidOptions(
            gravity=(0, 0, -9.8),
            enable_collision=True,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=True,
    )

    scene.add_entity(
        morph=gs.options.morphs.Plane(),
        material=gs.materials.Rigid(),
    )

    scene.add_entity(
        morph=gs.options.morphs.Sphere(
            pos=(0.0, 0.0, 2.0),
            radius=0.3,
        ),
        material=gs.materials.FEM.Elastic(
            E=50000.0,
            nu=0.3,
            rho=1000.0,
        ),
    )

    scene.build()

    for _ in range(2000):
        scene.step()

if __name__ == "__main__":
    main()
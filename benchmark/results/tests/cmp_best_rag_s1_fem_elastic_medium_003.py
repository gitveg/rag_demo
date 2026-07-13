import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=2e-3,
            substeps=5,
        ),
        fem_options=gs.options.FEMOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.5, 0.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        show_viewer=True,
    )

    # Flat ground
    scene.add_entity(gs.morphs.Plane())

    # Three squishy elastic spheres of different sizes
    radii = [0.1, 0.13, 0.16]
    x_positions = [-0.3, 0.0, 0.3]
    
    for r, x in zip(radii, x_positions):
        scene.add_entity(
            morph=gs.morphs.Sphere(pos=(x, 0.0, 1.0), radius=r),
            material=gs.materials.FEM.Elastic(E=50000, nu=0.3),
        )

    scene.build()

    for _ in range(400):
        scene.step()

if __name__ == "__main__":
    main()
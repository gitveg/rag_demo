import numpy as np
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
            camera_pos=(1.5, -1.5, 1.2),
            camera_lookat=(0, 0, 0.1),
            max_FPS=60,
        ),
        show_viewer=True,
    )

    # Flat ground plane
    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(),
    )

    # Soft elastic cube
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.075),
            size=(0.15, 0.15, 0.15),
        ),
        material=gs.materials.FEM.Elastic(
            E=1.0e5,
            nu=0.45,
            rho=1000.0,
            model="stable_neohookean",
        ),
    )

    # Rigid sphere dropped from above
    scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 0.45),
            radius=0.06,
        ),
        material=gs.materials.Rigid(rho=1500),
    )

    scene.build()

    for _ in range(300):
        scene.step()


if __name__ == "__main__":
    main()
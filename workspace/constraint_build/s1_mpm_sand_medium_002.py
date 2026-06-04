import numpy as np
import genesis as gs

def main():
    gs.init(seed=None, precision="32", logging_level="info")

    # Scene setup with MPM for sand
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=3e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=[-1.0, 0.0, -1.0],
            upper_bound=[1.0, 1.0, 1.0],
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, 2.0, 2.0),
            camera_lookat=(0.0, 0.3, 0.0),
        ),
        show_viewer=True,
        show_FPS=True,
    )

    # Sand layer (flat box of MPM particles)
    sand_material = gs.materials.MPM.Sand(
        rho=1500.0,          # sand density
        friction_angle=35,   # internal friction angle
    )
    sand = scene.add_entity(
        morph=gs.morphs.Box(
            size=(1.0, 0.15, 1.0),       # layer dimensions
            pos=(0.0, 0.075, 0.0),       # center at y=0.075
            euler=(0.0, 0.0, 0.0),
        ),
        material=sand_material,
    )

    # Rigid sphere
    sphere_material = gs.materials.Rigid(
        rho=200.0,
        friction=0.5,
    )
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            radius=0.1,
            pos=(0.0, 0.5, 0.0),
            euler=(0.0, 0.0, 0.0),
        ),
        material=sphere_material,
    )

    # Build the scene
    scene.build()

    # Simulate for 500 steps (about 1.5 seconds with dt=3e-3 and substeps=10)
    for i in range(500):
        scene.step()

if __name__ == "__main__":
    main()
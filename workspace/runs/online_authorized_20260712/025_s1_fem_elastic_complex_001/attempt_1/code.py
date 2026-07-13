import numpy as np
import genesis as gs

def main():
    ########################## init ##########################
    gs.init(backend=gs.gpu, logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            substeps=10,
            gravity=(0, 0, -9.8),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, 1.5, 1.0),
            camera_lookat=(0.25, 0.0, 0.2),
            camera_up=(0, 0, 1),
        ),
        show_viewer=True,
    )

    ########################## materials ##########################
    mat_soft = gs.materials.PBD.Elastic()

    ########################## beam (soft box) ##########################
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.25),
            size=(0.5, 0.05, 0.05),
        ),
        material=mat_soft,
        surface=gs.surfaces.Default(
            color=(0.3, 0.6, 1.0),
            vis_mode="visual",
        ),
    )

    ########################## bouncing sphere ##########################
    scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.25, 0.0, 0.5),
            radius=0.05,
        ),
        material=mat_soft,
        surface=gs.surfaces.Default(
            color=(1.0, 0.3, 0.3),
            vis_mode="visual",
        ),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## simulation loop ##########################
    for _ in range(2000):
        scene.step()

if __name__ == "__main__":
    main()
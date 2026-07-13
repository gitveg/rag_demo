import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(0.0, 0.0, 0.0),
            upper_bound=(1.0, 1.0, 1.0),
        ),
        vis_options=gs.options.VisOptions(
            visualize_mpm_boundary=True,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_fov=30,
            res=(960, 640),
        ),
        show_viewer=True,
    )

    # Fill the upper half of the cube with liquid particles
    scene.add_entity(
        gs.morphs.Box(
            pos=(0.5, 0.5, 0.75),
            size=(0.9, 0.9, 0.5),
        ),
        material=gs.materials.MPM.Liquid(),
    )

    scene.build()

    # Let the fluid settle under gravity
    for _ in range(1000):
        scene.step()

if __name__ == "__main__":
    main()
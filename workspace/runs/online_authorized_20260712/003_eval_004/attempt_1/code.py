import genesis as gs

def main():
    gs.init(backend=gs.gpu, logging_level="info")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            substeps=10,
            gravity=(0, 0, 0),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2, 2, 1.5),
            camera_lookat=(0, 0, 0.5),
            camera_up=(0, 0, 1),
        ),
        show_viewer=True,
    )

    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(
            pos=(0, 0, 0),
            size=(0.1, 0.1, 0.1),
        ),
        surface=gs.surfaces.Default(),
    )

    scene.build()

    for _ in range(200):
        scene.step()

if __name__ == "__main__":
    main()
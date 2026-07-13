import genesis as gs

def main():
    gs.init(backend=gs.gpu)
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            substeps=10,
            gravity=(0, 0, -9.8),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2, 2, 1.5),
            camera_lookat=(0, 0, 0.5),
            camera_up=(0, 0, 1),
        ),
        show_viewer=True,
    )

    mat_elastic = gs.materials.PBD.Elastic()

    beam = scene.add_entity(
        morph=gs.morphs.Box(pos=(0, 0, 0.5), size=(0.5, 0.1, 0.1)),
        material=mat_elastic,
    )
    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(pos=(0.6, 0.0, 0.6), radius=0.05),
        material=mat_elastic,
    )

    scene.build()

    for _ in range(1000):
        scene.step()

if __name__ == "__main__":
    main()
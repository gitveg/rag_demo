import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            substeps=10,
            gravity=(0, 0, -9.8),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, 2, 2),
            camera_lookat=(0, 0, 1),
            camera_up=(0, 0, 1),
        ),
        show_viewer=True,
    )

    plane = scene.add_entity(gs.morphs.Plane())

    bunny = scene.add_entity(
        material=gs.materials.PBD.Elastic(),
        morph=gs.morphs.Mesh(
            file='bunny.obj',
            pos=(0, 0, 2),
            scale=(0.001, 0.001, 0.001),
        ),
        surface=gs.surfaces.Default(color=(0.8, 0.6, 0.4, 1.0)),
    )

    scene.build()

    for _ in range(2000):
        scene.step()

if __name__ == "__main__":
    main()
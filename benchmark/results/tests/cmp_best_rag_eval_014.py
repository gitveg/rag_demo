import genesis as gs


def main():
    gs.init()
    scene = gs.Scene(
        fem_options=gs.options.FEMOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -3, 2),
            camera_lookat=(0, 0, 0.5),
        ),
        show_viewer=True,
    )
    # large static rigid box (fixed in place)
    scene.add_entity(
        gs.morphs.Box(pos=(0, 0, 0.25), size=(0.5, 0.5, 0.5), fixed=True),
        material=gs.materials.Rigid(),
    )
    # soft elastic box stacked on top (FEM)
    scene.add_entity(
        gs.morphs.Box(pos=(0, 0, 0.6), size=(0.2, 0.2, 0.2)),
        material=gs.materials.FEM.Elastic(),
    )
    scene.build()
    for _ in range(300):
        scene.step()


if __name__ == "__main__":
    main()
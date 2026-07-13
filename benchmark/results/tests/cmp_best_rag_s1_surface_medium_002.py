import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        show_viewer=True,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -3.5, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
    )

    # ground plane
    plane = scene.add_entity(gs.morphs.Plane())

    # matte red plastic cube (left)
    red_plastic = scene.add_entity(
        gs.morphs.Box(pos=(-0.15, 0.0, 0.12), size=(0.1, 0.1, 0.1), fixed=True),
        surface=gs.surfaces.Default(color=(1, 0, 0, 1)),
    )

    # rough concrete cube (center)
    concrete = scene.add_entity(
        gs.morphs.Box(pos=(0.0, 0.0, 0.12), size=(0.1, 0.1, 0.1), fixed=True),
        surface=gs.surfaces.Rough(color=(0.5, 0.5, 0.5, 1)),
    )

    # polished gold metal cube (right)
    gold_metal = scene.add_entity(
        gs.morphs.Box(pos=(0.15, 0.0, 0.12), size=(0.1, 0.1, 0.1), fixed=True),
        surface=gs.surfaces.Default(color=(1, 0.84, 0, 1)),
    )

    scene.build()

    # run for a while to display the scene
    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()
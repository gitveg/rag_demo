import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, -3.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=True,
    )

    plane = scene.add_entity(gs.morphs.Plane())

    cube = scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 0.2),
            size=(0.2, 0.2, 0.2),
        ),
        surface=gs.options.surfaces.Default(
            color=(0.75, 0.75, 0.75, 1.0),  # shiny metallic silver
        ),
    )

    cylinder = scene.add_entity(
        gs.morphs.Cylinder(
            pos=(0.5, 0.0, 0.2),
            radius=0.1,
            height=0.2,
        ),
        surface=gs.options.surfaces.Rough(
            color=(0.0, 0.0, 1.0, 1.0),  # matte blue plastic
        ),
    )

    scene.build()

    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()
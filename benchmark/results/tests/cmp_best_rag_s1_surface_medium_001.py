import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        show_viewer=True,
    )

    # Gray ground plane
    scene.add_entity(
        morph=gs.morphs.Plane(),
        surface=gs.options.surfaces.Rough(color=(0.5, 0.5, 0.5)),
    )

    # Red metallic sphere
    scene.add_entity(
        morph=gs.morphs.Sphere(
            radius=0.3,
            pos=(0.0, 0.0, 0.5),
        ),
        material=gs.materials.Rigid(),
        surface=gs.options.surfaces.Smooth(color=(1.0, 0.0, 0.0)),
    )

    # Yellow matte box
    scene.add_entity(
        morph=gs.morphs.Box(
            size=(0.4, 0.4, 0.4),
            pos=(1.0, 0.0, 0.5),
        ),
        material=gs.materials.Rigid(),
        surface=gs.options.surfaces.Rough(color=(1.0, 1.0, 0.0)),
    )

    scene.build()

    for _ in range(300):
        scene.step()


if __name__ == "__main__":
    main()
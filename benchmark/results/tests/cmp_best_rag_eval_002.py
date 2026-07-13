import genesis as gs


def main():
    gs.init()
    scene = gs.Scene(show_viewer=True)
    scene.add_entity(morph=gs.morphs.Plane())
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.5),
            size=(1.0, 1.0, 1.0),
            fixed=True,
        )
    )
    scene.build()

    for _ in range(100):
        scene.step()


if __name__ == "__main__":
    main()
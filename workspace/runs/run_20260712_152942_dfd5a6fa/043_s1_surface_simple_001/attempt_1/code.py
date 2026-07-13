import genesis as gs


def main():
    gs.init()

    scene = gs.Scene()

    # ground plane
    scene.add_entity(morph=gs.morphs.Plane())

    # blue sphere
    scene.add_entity(
        morph=gs.morphs.Sphere(pos=(0.0, 0.0, 0.5), radius=0.5),
        surface=gs.surfaces.Default(color=(0.0, 0.0, 1.0)),
    )

    scene.build()

    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()
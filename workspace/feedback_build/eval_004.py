import genesis as gs

def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(gravity=(0, 0, 0)),
    )

    scene.add_entity(
        gs.morphs.Box(
            pos=(0.0, 0.0, 0.0),
            size=(0.5, 0.5, 0.5),
        ),
    )

    scene.build()

    for _ in range(100):
        scene.step()

if __name__ == "__main__":
    main()
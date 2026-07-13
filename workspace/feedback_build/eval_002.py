import genesis as gs

def main():
    gs.init()
    scene = gs.Scene()
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0, 0, 0.5),
            size=(0.5, 0.5, 0.5),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
    )
    scene.build()

if __name__ == "__main__":
    main()
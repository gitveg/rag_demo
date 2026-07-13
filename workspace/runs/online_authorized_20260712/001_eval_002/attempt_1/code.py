import torch
import genesis as gs


def main():
    gs.init(seed=1)

    scene = gs.Scene(show_viewer=False)

    scene.add_entity(gs.morphs.Plane())

    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, 0.0, 0.5), size=(1.0, 1.0, 1.0), fixed=True),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5)),
    )

    scene.build()
    scene.step()

    print("Static rigid box obstacle created.")


if __name__ == "__main__":
    main()
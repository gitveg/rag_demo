import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        fem_options=gs.options.FEMOptions(),
        show_viewer=True,
    )

    plane = scene.add_entity(gs.morphs.Plane())
    cube = scene.add_entity(
        gs.morphs.Box(pos=(0.5, 0.5, 0.1), size=(0.2, 0.2, 0.2)),
        material=gs.materials.FEM.Elastic(),
    )
    sphere = scene.add_entity(
        gs.morphs.Sphere(pos=(0.5, 0.5, 0.5), radius=0.1),
        material=gs.materials.Rigid(),
    )

    scene.build()

    for _ in range(1000):
        scene.step()

if __name__ == "__main__":
    main()
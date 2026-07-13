import genesis as gs

def main():
    gs.init()

    scene = gs.Scene()

    # Ground plane
    scene.add_entity(morph=gs.morphs.Plane())

    # Matte red plastic cube (left)
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(-0.5, 0.0, 0.5),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Plastic(color=(0.8, 0.2, 0.2, 1.0)),
    )

    # Rough concrete cube (center, approximated with gray Default)
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.5),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5)),
    )

    # Polished gold metal cube (right, approximated with yellow Default)
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.5, 0.0, 0.5),
            size=(0.2, 0.2, 0.2),
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(1.0, 0.84, 0.0)),
    )

    # Camera to view the scene
    cam = scene.add_camera(
        res=(640, 480),
        pos=(1.5, -1.5, 1.2),
        lookat=(0, 0, 0.5),
        fov=40,
    )

    scene.build()

    # Run a few steps to let the scene settle
    for _ in range(200):
        scene.step()

if __name__ == "__main__":
    main()
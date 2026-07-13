import genesis as gs

def main():
    gs.init(backend=gs.cpu)

    scene = gs.Scene(show_viewer=True)

    # Ground plane
    scene.add_entity(morph=gs.morphs.Plane())

    # Red rigid box
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 1.0),
            size=(0.2, 0.2, 0.2),
        ),
        surface=gs.options.surfaces.Default(
            color=(1.0, 0.0, 0.0, 1.0),
        ),
    )

    # Blue rigid cylinder
    scene.add_entity(
        morph=gs.morphs.Cylinder(
            pos=(0.3, 0.0, 1.0),
            radius=0.1,
            height=0.3,
        ),
        surface=gs.options.surfaces.Default(
            color=(0.0, 0.0, 1.0, 1.0),
        ),
    )

    scene.build()

    # Run simulation
    for _ in range(200):
        scene.step()

if __name__ == "__main__":
    main()
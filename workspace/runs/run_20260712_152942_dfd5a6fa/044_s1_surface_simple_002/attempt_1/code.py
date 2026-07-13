import genesis as gs

def main():
    gs.init()
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            res=(800, 600),
        ),
    )

    # ground plane
    scene.add_entity(gs.morphs.Plane())

    # shiny metallic sphere
    scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 0.5),
            radius=0.2,
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8)),  # silver appearance
    )

    scene.build()
    for _ in range(100):
        scene.step()

if __name__ == "__main__":
    main()
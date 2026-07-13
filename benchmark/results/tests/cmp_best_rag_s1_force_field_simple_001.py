import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5.0, 5.0, 5.0),
            camera_lookat=(0.0, 0.0, 2.5),
        ),
        show_viewer=True,
    )

    sphere = scene.add_entity(
        morph=gs.options.morphs.Sphere(pos=(0.0, 0.0, 5.0), radius=0.5),
        material=gs.materials.Rigid(),
    )

    wind = gs.force_fields.Wind(
        direction=(1.0, 0.0, 0.0),
        strength=1.0,
        radius=100.0,
        center=(0.0, 0.0, 0.0),
    )
    scene.add_force_field(wind)

    scene.build()

    for _ in range(1000):
        scene.step()

if __name__ == "__main__":
    main()
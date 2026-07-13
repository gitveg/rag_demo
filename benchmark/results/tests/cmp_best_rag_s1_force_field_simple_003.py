import genesis as gs

def main():
    gs.init()
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.5, 0.0, 0.5),
        ),
        show_viewer=True,
    )

    # ground plane for reference
    scene.add_entity(
        morph=gs.options.morphs.Plane(),
        material=gs.materials.Rigid(),
    )

    # sphere with gravity compensation to hover
    scene.add_entity(
        morph=gs.options.morphs.Sphere(pos=(0.0, 0.0, 1.0), radius=0.2),
        material=gs.materials.Rigid(gravity_compensation=1.0),
    )

    scene.build()
    for _ in range(1000):
        scene.step()

if __name__ == "__main__":
    main()
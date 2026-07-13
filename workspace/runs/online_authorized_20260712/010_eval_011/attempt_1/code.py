import genesis as gs

def main():
    gs.init(backend=gs.cpu, precision="32")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.01,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -2, 0.5),
            camera_lookat=(0, 0, 0.5),
            max_FPS=60,
        ),
        show_viewer=True,
    )

    plane = scene.add_entity(gs.morphs.Plane())

    box_size = 0.1
    # place boxes with a tiny overlap (0.001 m) so they gently push apart
    box1 = scene.add_entity(
        material=gs.materials.Rigid(rho=200, gravity_compensation=1.0),
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.5),
            size=(box_size, box_size, box_size),
        ),
        surface=gs.surfaces.Default(color=(0.5, 1, 0.5)),
    )

    box2 = scene.add_entity(
        material=gs.materials.Rigid(rho=200, gravity_compensation=1.0),
        morph=gs.morphs.Box(
            pos=(0.099, 0.0, 0.5),
            size=(box_size, box_size, box_size),
        ),
        surface=gs.surfaces.Default(color=(0.8, 0.3, 0.2)),
    )

    scene.build()

    # let the contact solver resolve the penetration over several steps
    for _ in range(300):
        scene.step()

if __name__ == "__main__":
    main()